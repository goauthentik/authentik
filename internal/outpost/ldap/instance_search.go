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
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "filter_parse_fail",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "empty_bind_dn",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !strings.HasSuffix(req.BindDN, baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "invalid_bind_dn",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, pi.BaseDN)
	}

	pi.boundUsersMutex.RLock()
	flags, ok := pi.boundUsers[req.BindDN]
	pi.boundUsersMutex.RUnlock()
	if !ok {
		pi.log.Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "user_info_not_cached",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}

	if req.SearchRequest.Scope == ldap.ScopeBaseObject {
		pi.log.Debug("base scope, showing domain info")
		return pi.SearchBase(req, flags.CanSearch)
	}
	if !flags.CanSearch {
		pi.log.Debug("User can't search, showing info about user")
		return pi.SearchMe(req, flags)
	}
	accsp.Finish()

	parsedFilter, err := ldap.CompileFilter(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "filter_parse_fail",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}

	// Create a custom client to set additional headers
	c := api.NewAPIClient(pi.s.ac.Client.GetConfig())
	c.GetConfig().AddDefaultHeader("X-authentik-outpost-ldap-query", req.Filter)

	switch filterEntity {
	default:
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": pi.outpostName,
			"type":         "search",
			"reason":       "unhandled_filter_type",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, req.Filter)
	case "groupOfUniqueNames":
		fallthrough
	case "goauthentik.io/ldap/group":
		fallthrough
	case "goauthentik.io/ldap/virtual-group":
		fallthrough
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
	case "":
		fallthrough
	case "organizationalPerson":
		fallthrough
	case "inetOrgPerson":
		fallthrough
	case "goauthentik.io/ldap/user":
		fallthrough
	case UserObjectClass:
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
	dn := pi.GetUserDN(u.Username)
	attrs := AKAttrsToLDAP(u.Attributes)

	attrs = pi.ensureAttributes(attrs, map[string][]string{
		"memberOf": pi.GroupsForUser(u),
		// Old fields for backwards compatibility
		"accountStatus":                 {BoolToString(*u.IsActive)},
		"superuser":                     {BoolToString(u.IsSuperuser)},
		"goauthentik.io/ldap/active":    {BoolToString(*u.IsActive)},
		"goauthentik.io/ldap/superuser": {BoolToString(u.IsSuperuser)},
		"cn":                            {u.Username},
		"sAMAccountName":                {u.Username},
		"uid":                           {u.Uid},
		"name":                          {u.Name},
		"displayName":                   {u.Name},
		"mail":                          {*u.Email},
		"objectClass":                   {UserObjectClass, "organizationalPerson", "inetOrgPerson", "goauthentik.io/ldap/user"},
		"uidNumber":                     {pi.GetUidNumber(u)},
		"gidNumber":                     {pi.GetUidNumber(u)},
	})
	return &ldap.Entry{DN: dn, Attributes: attrs}
}

func (pi *ProviderInstance) GroupEntry(g LDAPGroup) *ldap.Entry {
	attrs := AKAttrsToLDAP(g.akAttributes)

	objectClass := []string{GroupObjectClass, "groupOfUniqueNames", "goauthentik.io/ldap/group"}
	if g.isVirtualGroup {
		objectClass = append(objectClass, "goauthentik.io/ldap/virtual-group")
	}

	attrs = pi.ensureAttributes(attrs, map[string][]string{
		"objectClass":                   objectClass,
		"member":                        g.member,
		"goauthentik.io/ldap/superuser": {BoolToString(g.isSuperuser)},
		"cn":                            {g.cn},
		"uid":                           {g.uid},
		"sAMAccountName":                {g.cn},
		"gidNumber":                     {g.gidNumber},
	})
	return &ldap.Entry{DN: g.dn, Attributes: attrs}
}
