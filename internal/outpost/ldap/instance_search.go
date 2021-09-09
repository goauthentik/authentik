package ldap

import (
	"errors"
	"fmt"
	"strings"
	"sync"

	"github.com/getsentry/sentry-go"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/utils"
)

func (pi *ProviderInstance) SearchMe(req SearchRequest, f UserFlags) (ldap.ServerSearchResult, error) {
	if f.UserInfo == nil {
		u, _, err := pi.s.ac.Client.CoreApi.CoreUsersRetrieve(req.ctx, f.UserPk).Execute()
		if err != nil {
			req.log.WithError(err).Warning("Failed to get user info")
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("failed to get userinfo")
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
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "filter_parse_fail",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "empty_bind_dn",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !strings.HasSuffix(req.BindDN, baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "invalid_bind_dn",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, pi.BaseDN)
	}

	pi.boundUsersMutex.RLock()
	flags, ok := pi.boundUsers[req.BindDN]
	pi.boundUsersMutex.RUnlock()
	if !ok {
		pi.log.Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "user_info_not_cached",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	if !flags.CanSearch {
		pi.log.Debug("User can't search, showing info about user")
		return pi.SearchMe(req, flags)
	}
	accsp.Finish()

	parsedFilter, err := ldap.CompileFilter(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "filter_parse_fail",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}

	// Create a custom client to set additional headers
	c := api.NewAPIClient(pi.s.ac.Client.GetConfig())
	c.GetConfig().AddDefaultHeader("X-authentik-outpost-ldap-query", req.Filter)

	switch filterEntity {
	default:
		metrics.RequestsRejected.With(prometheus.Labels{
			"type":   "search",
			"reason": "unhandled_filter_type",
			"dn":     req.BindDN,
			"client": utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, req.Filter)
	case GroupObjectClass:
		wg := sync.WaitGroup{}
		wg.Add(2)

		gEntries := make([]*ldap.Entry, 0)
		uEntries := make([]*ldap.Entry, 0)

		go func() {
			defer wg.Done()
			gapisp := sentry.StartSpan(req.ctx, "authentik.providers.ldap.search.api_group")
			searchReq, skip := parseFilterForGroup(c.CoreApi.CoreGroupsList(gapisp.Context()), parsedFilter, false)
			if skip {
				pi.log.Trace("Skip backend request")
				return
			}
			groups, _, err := searchReq.Execute()
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
			searchReq, skip := parseFilterForUser(c.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter, false)
			if skip {
				pi.log.Trace("Skip backend request")
				return
			}
			users, _, err := searchReq.Execute()
			uapisp.Finish()
			if err != nil {
				req.log.WithError(err).Warning("failed to get users")
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
		searchReq, skip := parseFilterForUser(c.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter, false)
		if skip {
			pi.log.Trace("Skip backend request")
			return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
		}
		users, _, err := searchReq.Execute()
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
			Name:   "sAMAccountName",
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
			Name:   "sAMAccountName",
			Values: []string{g.cn},
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
