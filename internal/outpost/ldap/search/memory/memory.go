package memory

import (
	"context"
	"errors"
	"fmt"
	"strings"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/group"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/search/direct"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
	"goauthentik.io/internal/outpost/ldap/utils/paginator"
)

type MemorySearcher struct {
	si  server.LDAPServerInstance
	log *log.Entry
	ds  *direct.DirectSearcher

	users  []api.User
	groups []api.Group
}

func NewMemorySearcher(si server.LDAPServerInstance) *MemorySearcher {
	ms := &MemorySearcher{
		si:  si,
		log: log.WithField("logger", "authentik.outpost.ldap.searcher.memory"),
		ds:  direct.NewDirectSearcher(si),
	}
	ms.log.Debug("initialised memory searcher")
	ms.users = paginator.FetchUsers(ms.si.GetAPIClient().CoreApi.CoreUsersList(context.TODO()))
	ms.groups = paginator.FetchGroups(ms.si.GetAPIClient().CoreApi.CoreGroupsList(context.TODO()))
	return ms
}

func (ms *MemorySearcher) SearchBase(req *search.Request) (ldap.ServerSearchResult, error) {
	return ms.ds.SearchBase(req)
}

func (ms *MemorySearcher) SearchSubschema(req *search.Request) (ldap.ServerSearchResult, error) {
	return ms.ds.SearchSubschema(req)
}

func (ms *MemorySearcher) Search(req *search.Request) (ldap.ServerSearchResult, error) {
	accsp := sentry.StartSpan(req.Context(), "authentik.providers.ldap.search.check_access")
	baseDN := ms.si.GetBaseDN()

	if len(req.BindDN) < 1 {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "empty_bind_dn",
			"app":          ms.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", req.BindDN)
	}
	if !utils.HasSuffixNoCase(req.BindDN, ","+baseDN) {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "invalid_bind_dn",
			"app":          ms.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", req.BindDN, ms.si.GetBaseDN())
	}

	flags := ms.si.GetFlags(req.BindDN)
	if flags == nil {
		req.Log().Debug("User info not cached")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": ms.si.GetOutpostName(),
			"type":         "search",
			"reason":       "user_info_not_cached",
			"app":          ms.si.GetAppSlug(),
		}).Inc()
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	accsp.Finish()

	entries := make([]*ldap.Entry, 0)

	scope := req.SearchRequest.Scope
	needUsers, needGroups := ms.si.GetNeededObjects(scope, req.BaseDN, req.FilterObjectClass)

	if scope >= 0 && strings.EqualFold(req.BaseDN, baseDN) {
		if utils.IncludeObjectClass(req.FilterObjectClass, constants.GetDomainOCs()) {
			rootEntries, _ := ms.SearchBase(req)
			for _, e := range rootEntries.Entries {
				e.DN = ms.si.GetBaseDN()
				entries = append(entries, e)
			}
		}

		scope -= 1 // Bring it from WholeSubtree to SingleLevel and so on
	}

	var users *[]api.User
	var groups []*group.LDAPGroup
	var err error

	if needUsers {
		if flags.CanSearch {
			users = &ms.users
		} else {
			u := make([]api.User, 1)
			if flags.UserInfo == nil {
				for i, u := range ms.users {
					if u.Pk == flags.UserPk {
						flags.UserInfo = &ms.users[i]
					}
				}

				if flags.UserInfo == nil {
					req.Log().WithField("pk", flags.UserPk).Warning("User with pk is not in local cache")
					err = fmt.Errorf("failed to get userinfo")
				}
			} else {
				u[0] = *flags.UserInfo
			}
			users = &u
		}
	}

	if needGroups {
		groups = make([]*group.LDAPGroup, 0)

		for _, g := range ms.groups {
			if flags.CanSearch {
				groups = append(groups, group.FromAPIGroup(g, ms.si))
			} else {
				// If the user cannot search, we're going to only return
				// the groups they're in _and_ only return themselves
				// as a member.
				for _, u := range g.UsersObj {
					if flags.UserPk == u.Pk {
						//TODO: Is there a better way to clone this object?
						fg := api.NewGroup(g.Pk, g.NumPk, g.Name, g.ParentName, []api.GroupMember{u})
						fg.SetUsers([]int32{flags.UserPk})
						if g.Parent.IsSet() {
							fg.SetParent(*g.Parent.Get())
						}
						fg.SetAttributes(g.Attributes)
						fg.SetIsSuperuser(*g.IsSuperuser)
						groups = append(groups, group.FromAPIGroup(*fg, ms.si))
						break
					}
				}
			}
		}
	}

	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, err
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ms.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ms.si.GetBaseUserDN())) {
		singleu := utils.HasSuffixNoCase(req.BaseDN, ","+ms.si.GetBaseUserDN())

		if !singleu && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(req.FilterObjectClass, ms.si.GetBaseUserDN(), constants.OUUsers))
			scope -= 1
		}

		if scope >= 0 && users != nil && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetUserOCs()) {
			for _, u := range *users {
				entry := ms.si.UserEntry(u)
				if strings.EqualFold(req.BaseDN, entry.DN) || !singleu {
					entries = append(entries, entry)
				}
			}
		}

		scope += 1 // Return the scope to what it was before we descended
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ms.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ms.si.GetBaseGroupDN())) {
		singleg := utils.HasSuffixNoCase(req.BaseDN, ","+ms.si.GetBaseGroupDN())

		if !singleg && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(req.FilterObjectClass, ms.si.GetBaseGroupDN(), constants.OUGroups))
			scope -= 1
		}

		if scope >= 0 && groups != nil && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetGroupOCs()) {
			for _, g := range groups {
				if strings.EqualFold(req.BaseDN, g.DN) || !singleg {
					entries = append(entries, g.Entry())
				}
			}
		}

		scope += 1 // Return the scope to what it was before we descended
	}

	if scope >= 0 && (strings.EqualFold(req.BaseDN, ms.si.GetBaseDN()) || utils.HasSuffixNoCase(req.BaseDN, ms.si.GetBaseVirtualGroupDN())) {
		singlevg := utils.HasSuffixNoCase(req.BaseDN, ","+ms.si.GetBaseVirtualGroupDN())

		if !singlevg && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetContainerOCs()) {
			entries = append(entries, utils.GetContainerEntry(req.FilterObjectClass, ms.si.GetBaseVirtualGroupDN(), constants.OUVirtualGroups))
			scope -= 1
		}

		if scope >= 0 && users != nil && utils.IncludeObjectClass(req.FilterObjectClass, constants.GetVirtualGroupOCs()) {
			for _, u := range *users {
				entry := group.FromAPIUser(u, ms.si).Entry()
				if strings.EqualFold(req.BaseDN, entry.DN) || !singlevg {
					entries = append(entries, entry)
				}
			}
		}
	}

	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
