package direct

import (
	"errors"
	"fmt"
	"strings"

	log "github.com/sirupsen/logrus"
	"golang.org/x/sync/errgroup"

	"github.com/getsentry/sentry-go"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/group"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
	"goauthentik.io/internal/outpost/ldap/utils/paginator"
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

func (ds *DirectSearcher) Search(req *search.Request) (ldap.ServerSearchResult, error) {
	accsp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.check_access")
	baseDN := ds.si.GetBaseDN()

	filterOC, err := ldap.GetFilterObjectClass(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "filter_parse_fail",
			"app":          ds.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}
	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "empty_bind_dn",
			"app":          ds.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !utils.HasSuffixNoCase(req.BindDN, ","+baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "invalid_bind_dn",
			"app":          ds.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, ds.si.GetBaseDN())
	}

	flags := ds.si.GetFlags(req.BindDN)
	if flags == nil {
		req.Log().Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "user_info_not_cached",
			"app":          ds.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	accsp.Finish()

	parsedFilter, err := ldap.CompileFilter(req.Filter)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ds.si.GetOutpostName(),
			"type":         "search",
			"reason":       "filter_parse_fail",
			"app":          ds.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", req.Filter)
	}

	entries := make([]*ldap.Entry, 0)

	// Create a custom client to set additional headers
	c := api.NewAPIClient(ds.si.GetAPIClient().GetConfig())
	c.GetConfig().AddDefaultHeader("X-authentik-outpost-ldap-query", req.Filter)

	scope := req.SearchRequest.Scope
	needUsers, needGroups := ds.si.GetNeededObjects(scope, req.BaseDN, filterOC)

	if scope >= 0 && strings.EqualFold(req.BaseDN, baseDN) {
		if utils.IncludeObjectClass(filterOC, constants.GetDomainOCs()) {
			entries = append(entries, ds.si.GetBaseEntry())
		}

		scope -= 1 // Bring it from WholeSubtree to SingleLevel and so on
	}

	var users *[]api.User
	var groups *[]api.Group

	errs, errCtx := errgroup.WithContext(req.Context())

	if needUsers {
		errs.Go(func() error {
			if flags.CanSearch {
				uapisp := sentry.StartSpan(errCtx, "authentik.providers.ldap.search.api_user")
				searchReq, skip := utils.ParseFilterForUser(c.CoreApi.CoreUsersList(uapisp.Context()), parsedFilter, false)

				if skip {
					req.Log().Trace("Skip backend request")
					return nil
				}

				u := paginator.FetchUsers(searchReq)
				uapisp.Finish()

				users = &u
			} else {
				if flags.UserInfo == nil {
					uapisp := sentry.StartSpan(errCtx, "authentik.providers.ldap.search.api_user")
					u, _, err := c.CoreApi.CoreUsersRetrieve(uapisp.Context(), flags.UserPk).Execute()
					uapisp.Finish()

					if err != nil {
						req.Log().WithError(err).Warning("Failed to get user info")
						return fmt.Errorf("failed to get userinfo")
					}

					flags.UserInfo = u
				}

				u := make([]api.User, 1)
				u[0] = *flags.UserInfo

				users = &u
			}
			return nil
		})
	}

	if needGroups {
		errs.Go(func() error {
			gapisp := sentry.StartSpan(errCtx, "authentik.providers.ldap.search.api_group")
			searchReq, skip := utils.ParseFilterForGroup(c.CoreApi.CoreGroupsList(gapisp.Context()), parsedFilter, false)
			if skip {
				req.Log().Trace("Skip backend request")
				return nil
			}

			if !flags.CanSearch {
				// If they can't search, filter all groups by those they're a member of
				searchReq = searchReq.MembersByPk([]int32{flags.UserPk})
			}

			g := paginator.FetchGroups(searchReq)
			gapisp.Finish()
			req.Log().WithField("count", len(g)).Trace("Got results from API")

			if !flags.CanSearch {
				for i, results := range g {
					// If they can't search, remove any users from the group results except the one we're looking for.
					g[i].Users = []int32{flags.UserPk}
					for _, u := range results.UsersObj {
						if u.Pk == flags.UserPk {
							g[i].UsersObj = []api.GroupMember{u}
							break
						}
					}
				}
			}

			groups = &g
			return nil
		})
	}

	err = errs.Wait()

	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, err
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ds.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ds.si.GetBaseUserDN())) {
		singleu := utils.HasSuffixNoCase(req.BaseDN, ","+ds.si.GetBaseUserDN())

		if !singleu && utils.IncludeObjectClass(filterOC, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(filterOC, ds.si.GetBaseUserDN(), constants.OUUsers))
			scope -= 1
		}

		if scope >= 0 && users != nil && utils.IncludeObjectClass(filterOC, constants.GetUserOCs()) {
			for _, u := range *users {
				entry := ds.si.UserEntry(u)
				if strings.EqualFold(req.BaseDN, entry.DN) || !singleu {
					entries = append(entries, entry)
				}
			}
		}

		scope += 1 // Return the scope to what it was before we descended
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ds.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ds.si.GetBaseGroupDN())) {
		singleg := utils.HasSuffixNoCase(req.BaseDN, ","+ds.si.GetBaseGroupDN())

		if !singleg && utils.IncludeObjectClass(filterOC, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(filterOC, ds.si.GetBaseGroupDN(), constants.OUGroups))
			scope -= 1
		}

		if scope >= 0 && groups != nil && utils.IncludeObjectClass(filterOC, constants.GetGroupOCs()) {
			for _, g := range *groups {
				entry := group.FromAPIGroup(g, ds.si).Entry()
				if strings.EqualFold(req.BaseDN, entry.DN) || !singleg {
					entries = append(entries, entry)
				}
			}
		}

		scope += 1 // Return the scope to what it was before we descended
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ds.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ds.si.GetBaseVirtualGroupDN())) {
		singlevg := utils.HasSuffixNoCase(req.BaseDN, ","+ds.si.GetBaseVirtualGroupDN())

		if !singlevg && utils.IncludeObjectClass(filterOC, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(filterOC, ds.si.GetBaseVirtualGroupDN(), constants.OUVirtualGroups))
			scope -= 1
		}

		if scope >= 0 && users != nil && utils.IncludeObjectClass(filterOC, constants.GetVirtualGroupOCs()) {
			for _, u := range *users {
				entry := group.FromAPIUser(u, ds.si).Entry()
				if strings.EqualFold(req.BaseDN, entry.DN) || !singlevg {
					entries = append(entries, entry)
				}
			}
		}
	}

	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
