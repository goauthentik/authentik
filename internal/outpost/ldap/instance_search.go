package ldap

import (
	"errors"
	"fmt"
	"strings"
	"sync"

	"github.com/getsentry/sentry-go"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
)

func (pi *ProviderInstance) SearchMe(req SearchRequest, f UserFlags) (ldap.ServerSearchResult, error) {
	if f.UserInfo == nil {
		u, _, err := pi.s.ac.Client.CoreApi.CoreUsersRetrieve(req.ctx, f.UserInfo.Pk).Execute()
		if err != nil {
			req.log.WithError(err).Warning("Failed to get user info")
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Failed to get userinfo")
		}
		f.UserInfo = &u
	}
	entries := make([]*ldap.Entry, 1)
	entries[0] = pi.UserEntry(*f.UserInfo)
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}

func (pi *ProviderInstance) Search(req SearchRequest) (ldap.ServerSearchResult, error) {
	accsp := sentry.StartSpan(req.ctx, "authentik.providers.ldap.search.check_access")
	baseDN := strings.ToLower("," + pi.BaseDN)

	entries := []*ldap.Entry{}
	filterEntity, err := ldap.GetFilterObjectClass(req.Filter)
	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !strings.HasSuffix(req.BindDN, baseDN) {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, pi.BaseDN)
	}

	pi.boundUsersMutex.RLock()
	flags, ok := pi.boundUsers[req.BindDN]
	pi.boundUsersMutex.RUnlock()
	if !ok {
		pi.log.Debug("User info not cached")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	if !flags.CanSearch {
		pi.log.Debug("User can't search, showing info about user")
		return pi.SearchMe(req, flags)
	}
	accsp.Finish()

	parsedFilter, err := ldap.CompileFilter(req.Filter)
	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}

	switch filterEntity {
	default:
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, req.Filter)
	case GroupObjectClass:
		wg := sync.WaitGroup{}
		wg.Add(2)

		gEntries := make([]*ldap.Entry, 0)
		uEntries := make([]*ldap.Entry, 0)

		go func() {
			defer wg.Done()
			gapisp := sentry.StartSpan(req.ctx, "authentik.providers.ldap.search.api_group")
			groups, _, err := parseFilterForGroup(pi.s.ac.Client.CoreApi.CoreGroupsList(gapisp.Context()), parsedFilter).Execute()
			gapisp.Finish()
			if err != nil {
				req.log.WithError(err).Warning("failed to get groups")
				return
			}
			pi.log.WithField("count", len(groups.Results)).Trace("Got results from API")

			for _, g := range groups.Results {
				gEntries = append(gEntries, pi.GroupEntry(pi.APIGroupToLDAPGroup(g)))
			}
		}()

		go func() {
			defer wg.Done()
			uapisp := sentry.StartSpan(req.ctx, "authentik.providers.ldap.search.api_user")
			users, _, err := parseFilterForUser(pi.s.ac.Client.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter).Execute()
			uapisp.Finish()
			if err != nil {
				req.log.WithError(err).Warning("failed to get groups")
				return
			}

			for _, u := range users.Results {
				uEntries = append(uEntries, pi.GroupEntry(pi.APIUserToLDAPGroup(u)))
			}
		}()
		wg.Wait()
		entries = append(gEntries, uEntries...)
	case UserObjectClass, "":
		uapisp := sentry.StartSpan(req.ctx, "authentik.providers.ldap.search.api_user")
		users, _, err := parseFilterForUser(pi.s.ac.Client.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter).Execute()
		uapisp.Finish()

		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		for _, u := range users.Results {
			entries = append(entries, pi.UserEntry(u))
		}
	}
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}

func (pi *ProviderInstance) UserEntry(u api.User) *ldap.Entry {
	attrs := []*ldap.EntryAttribute{
		{
			Name:   "cn",
			Values: []string{u.Username},
		},
		{
			Name:   "uid",
			Values: []string{u.Uid},
		},
		{
			Name:   "name",
			Values: []string{u.Name},
		},
		{
			Name:   "displayName",
			Values: []string{u.Name},
		},
		{
			Name:   "mail",
			Values: []string{*u.Email},
		},
		{
			Name:   "objectClass",
			Values: []string{UserObjectClass, "organizationalPerson", "goauthentik.io/ldap/user"},
		},
		{
			Name:   "uidNumber",
			Values: []string{pi.GetUidNumber(u)},
		},
		{
			Name:   "gidNumber",
			Values: []string{pi.GetUidNumber(u)},
		},
	}

	attrs = append(attrs, &ldap.EntryAttribute{Name: "memberOf", Values: pi.GroupsForUser(u)})

	// Old fields for backwards compatibility
	attrs = append(attrs, &ldap.EntryAttribute{Name: "accountStatus", Values: []string{BoolToString(*u.IsActive)}})
	attrs = append(attrs, &ldap.EntryAttribute{Name: "superuser", Values: []string{BoolToString(u.IsSuperuser)}})

	attrs = append(attrs, &ldap.EntryAttribute{Name: "goauthentik.io/ldap/active", Values: []string{BoolToString(*u.IsActive)}})
	attrs = append(attrs, &ldap.EntryAttribute{Name: "goauthentik.io/ldap/superuser", Values: []string{BoolToString(u.IsSuperuser)}})

	attrs = append(attrs, AKAttrsToLDAP(u.Attributes)...)

	dn := pi.GetUserDN(u.Username)

	return &ldap.Entry{DN: dn, Attributes: attrs}
}

func (pi *ProviderInstance) GroupEntry(g LDAPGroup) *ldap.Entry {
	attrs := []*ldap.EntryAttribute{
		{
			Name:   "cn",
			Values: []string{g.cn},
		},
		{
			Name:   "uid",
			Values: []string{g.uid},
		},
		{
			Name:   "gidNumber",
			Values: []string{g.gidNumber},
		},
	}

	if g.isVirtualGroup {
		attrs = append(attrs, &ldap.EntryAttribute{
			Name:   "objectClass",
			Values: []string{GroupObjectClass, "goauthentik.io/ldap/group", "goauthentik.io/ldap/virtual-group"},
		})
	} else {
		attrs = append(attrs, &ldap.EntryAttribute{
			Name:   "objectClass",
			Values: []string{GroupObjectClass, "goauthentik.io/ldap/group"},
		})
	}

	attrs = append(attrs, &ldap.EntryAttribute{Name: "member", Values: g.member})
	attrs = append(attrs, &ldap.EntryAttribute{Name: "goauthentik.io/ldap/superuser", Values: []string{BoolToString(g.isSuperuser)}})

	if g.akAttributes != nil {
		attrs = append(attrs, AKAttrsToLDAP(g.akAttributes)...)
	}

	return &ldap.Entry{DN: g.dn, Attributes: attrs}
}
