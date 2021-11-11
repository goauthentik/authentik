package memory

import (
	"errors"
	"fmt"
	"strings"

	"github.com/getsentry/sentry-go"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/group"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/server"
)

type MemorySearcher struct {
	si  server.LDAPServerInstance
	log *log.Entry

	users  []api.User
	groups []api.Group
}

func NewMemorySearcher(si server.LDAPServerInstance) *MemorySearcher {
	ms := &MemorySearcher{
		si:  si,
		log: log.WithField("logger", "authentik.outpost.ldap.searcher.memory"),
	}
	ms.log.Info("initialised memory searcher")
	ms.users = ms.FetchUsers()
	ms.groups = ms.FetchGroups()
	return ms
}

func (ms *MemorySearcher) SearchMe(req *search.Request, f flags.UserFlags) (ldap.ServerSearchResult, error) {
	if f.UserInfo == nil {
		for _, u := range ms.users {
			if u.Pk == f.UserPk {
				f.UserInfo = &u
			}
		}
		if f.UserInfo == nil {
			req.Log().WithField("pk", f.UserPk).Warning("User with pk is not in local cache")
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("failed to get userinfo")
		}
	}
	entries := make([]*ldap.Entry, 1)
	entries[0] = ms.si.UserEntry(*f.UserInfo)
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}

func (ms *MemorySearcher) Search(req *search.Request) (ldap.ServerSearchResult, error) {
	accsp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.check_access")
	baseDN := strings.ToLower("," + ms.si.GetBaseDN())

	entries := []*ldap.Entry{}
	filterEntity, err := ldap.GetFilterObjectClass(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "filter_parse_fail",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "empty_bind_dn",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !strings.HasSuffix(req.BindDN, baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "invalid_bind_dn",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, ms.si.GetBaseDN())
	}

	flags, ok := ms.si.GetFlags(req.BindDN)
	if !ok {
		req.Log().Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "user_info_not_cached",
			"dn":           req.BindDN,
			"client":       req.RemoteAddr(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}

	if req.Scope == ldap.ScopeBaseObject {
		req.Log().Debug("base scope, showing domain info")
		return ms.SearchBase(req, flags.CanSearch)
	}
	if !flags.CanSearch {
		req.Log().Debug("User can't search, showing info about user")
		return ms.SearchMe(req, flags)
	}
	accsp.Finish()

	switch filterEntity {
	default:
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
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
		for _, g := range ms.groups {
			entries = append(entries, group.FromAPIGroup(g, ms.si).Entry())
		}
		for _, u := range ms.users {
			entries = append(entries, group.FromAPIUser(u, ms.si).Entry())
		}
	case "":
		fallthrough
	case constants.OCOrgPerson:
		fallthrough
	case constants.OCInetOrgPerson:
		fallthrough
	case constants.OCAKUser:
		fallthrough
	case constants.OCUser:
		for _, u := range ms.users {
			entries = append(entries, ms.si.UserEntry(u))
		}
	}
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
