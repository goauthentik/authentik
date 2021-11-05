package direct

import (
	"errors"
	"fmt"
	"strings"
	"sync"

	log "github.com/sirupsen/logrus"

	"github.com/getsentry/sentry-go"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/group"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
)

type DirectSearcher struct {
	si  server.LDAPServerInstance
	log *log.Entry
}

func NewDirectSearcher(si server.LDAPServerInstance) *DirectSearcher {
	ds := &DirectSearcher{
		si:  si,
		log: log.WithField("logger", "authentik.outpost.ldap.searcher.direct"),
	}
	ds.log.Info("initialised direct searcher")
	return ds
}

func (ds *DirectSearcher) SearchMe(req *search.Request, f flags.UserFlags) (ldap.ServerSearchResult, error) {
	if f.UserInfo == nil {
		u, _, err := ds.si.GetAPIClient().CoreApi.CoreUsersRetrieve(req.Context(), f.UserPk).Execute()
		if err != nil {
			req.Log().WithError(err).Warning("Failed to get user info")
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("failed to get userinfo")
		}
		f.UserInfo = &u
	}
	entries := make([]*ldap.Entry, 1)
	entries[0] = ds.si.UserEntry(*f.UserInfo)
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}

func (ds *DirectSearcher) Search(req *search.Request) (ldap.ServerSearchResult, error) {
	accsp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.check_access")
	baseDN := strings.ToLower("," + ds.si.GetBaseDN())

	entries := []*ldap.Entry{}
	filterEntity, err := ldap.GetFilterObjectClass(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "filter_parse_fail",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "empty_bind_dn",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !strings.HasSuffix(req.BindDN, baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "invalid_bind_dn",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, ds.si.GetBaseDN())
	}

	flags, ok := ds.si.GetFlags(req.BindDN)
	if !ok {
		req.Log().Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "user_info_not_cached",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}

	if req.Scope == ldap.ScopeBaseObject {
		req.Log().Debug("base scope, showing domain info")
		return ds.SearchBase(req, flags.CanSearch)
	}
	if !flags.CanSearch {
		req.Log().Debug("User can't search, showing info about user")
		return ds.SearchMe(req, flags)
	}
	accsp.Finish()

	parsedFilter, err := ldap.CompileFilter(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "filter_parse_fail",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}

	// Create a custom client to set additional headers
	c := api.NewAPIClient(ds.si.GetAPIClient().GetConfig())
	c.GetConfig().AddDefaultHeader("X-authentik-outpost-ldap-query", req.Filter)

	switch filterEntity {
	default:
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "unhandled_filter_type",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, req.Filter)
	case constants.OCGroupOfUniqueNames:
		fallthrough
	case constants.OCAKGroup:
		fallthrough
	case constants.OCAKVirtualGroup:
		fallthrough
	case constants.OCGroup:
		wg := sync.WaitGroup{}
		wg.Add(2)

		gEntries := make([]*ldap.Entry, 0)
		uEntries := make([]*ldap.Entry, 0)

		go func() {
			defer wg.Done()
			gapisp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.api_group")
			searchReq, skip := utils.ParseFilterForGroup(c.CoreApi.CoreGroupsList(gapisp.Context()), parsedFilter, false)
			if skip {
				req.Log().Trace("Skip backend request")
				return
			}
			groups, _, err := searchReq.Execute()
			gapisp.Finish()
			if err != nil {
				req.Log().WithError(err).Warning("failed to get groups")
				return
			}
			req.Log().WithField("count", len(groups.Results)).Trace("Got results from API")

			for _, g := range groups.Results {
				gEntries = append(gEntries, group.FromAPIGroup(g, ds.si).Entry())
			}
		}()

		go func() {
			defer wg.Done()
			uapisp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.api_user")
			searchReq, skip := utils.ParseFilterForUser(c.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter, false)
			if skip {
				req.Log().Trace("Skip backend request")
				return
			}
			users, _, err := searchReq.Execute()
			uapisp.Finish()
			if err != nil {
				req.Log().WithError(err).Warning("failed to get users")
				return
			}

			for _, u := range users.Results {
				uEntries = append(uEntries, group.FromAPIUser(u, ds.si).Entry())
			}
		}()
		wg.Wait()
		entries = append(gEntries, uEntries...)
	case "":
		fallthrough
	case constants.OCOrgPerson:
		fallthrough
	case constants.OCInetOrgPerson:
		fallthrough
	case constants.OCAKUser:
		fallthrough
	case constants.OCUser:
		uapisp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.api_user")
		searchReq, skip := utils.ParseFilterForUser(c.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter, false)
		if skip {
			req.Log().Trace("Skip backend request")
			return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
		}
		users, _, err := searchReq.Execute()
		uapisp.Finish()

		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		for _, u := range users.Results {
			entries = append(entries, ds.si.UserEntry(u))
		}
	}
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
