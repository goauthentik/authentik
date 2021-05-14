package ldap

import (
	"errors"
	"fmt"
	"net"
	"strings"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/pkg/client/core"
)

func (pi *ProviderInstance) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	bindDN = strings.ToLower(bindDN)
	baseDN := strings.ToLower("," + pi.BaseDN)

	entries := []*ldap.Entry{}
	filterEntity, err := ldap.GetFilterObjectClass(searchReq.Filter)
	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", searchReq.Filter)
	}
	if len(bindDN) < 1 {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", bindDN)
	}
	if !strings.HasSuffix(bindDN, baseDN) {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", bindDN, pi.BaseDN)
	}

	pi.boundUsersMutex.RLock()
	defer pi.boundUsersMutex.RUnlock()
	flags, ok := pi.boundUsers[bindDN]
	pi.log.WithField("bindDN", bindDN).WithField("ok", ok).Debugf("%+v\n", flags)
	if !ok {
		pi.log.Debug("User info not cached")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	if !flags.CanSearch {
		pi.log.Debug("User can't search")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}

	switch filterEntity {
	default:
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, searchReq.Filter)
	case GroupObjectClass:
		groups, err := pi.s.ac.Client.Core.CoreGroupsList(core.NewCoreGroupsListParams(), pi.s.ac.Auth)
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		pi.log.WithField("count", len(groups.Payload.Results)).Trace("Got results from API")
		for _, g := range groups.Payload.Results {
			attrs := []*ldap.EntryAttribute{
				{
					Name:   "cn",
					Values: []string{*g.Name},
				},
				{
					Name:   "uid",
					Values: []string{string(g.Pk)},
				},
				{
					Name:   "objectClass",
					Values: []string{GroupObjectClass, "goauthentik.io/ldap/group"},
				},
			}
			attrs = append(attrs, AKAttrsToLDAP(g.Attributes)...)

			dn := pi.GetGroupDN(g)
			entries = append(entries, &ldap.Entry{DN: dn, Attributes: attrs})
		}
	case UserObjectClass, "":
		users, err := pi.s.ac.Client.Core.CoreUsersList(core.NewCoreUsersListParams(), pi.s.ac.Auth)
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		for _, u := range users.Payload.Results {
			attrs := []*ldap.EntryAttribute{
				{
					Name:   "cn",
					Values: []string{*u.Username},
				},
				{
					Name:   "uid",
					Values: []string{u.UID},
				},
				{
					Name:   "name",
					Values: []string{*u.Name},
				},
				{
					Name:   "displayName",
					Values: []string{*u.Name},
				},
				{
					Name:   "mail",
					Values: []string{u.Email.String()},
				},
				{
					Name:   "objectClass",
					Values: []string{UserObjectClass, "organizationalPerson", "goauthentik.io/ldap/user"},
				},
			}

			if u.IsActive {
				attrs = append(attrs, &ldap.EntryAttribute{Name: "accountStatus", Values: []string{"inactive"}})
			} else {
				attrs = append(attrs, &ldap.EntryAttribute{Name: "accountStatus", Values: []string{"active"}})
			}

			if *u.IsSuperuser {
				attrs = append(attrs, &ldap.EntryAttribute{Name: "superuser", Values: []string{"inactive"}})
			} else {
				attrs = append(attrs, &ldap.EntryAttribute{Name: "superuser", Values: []string{"active"}})
			}

			attrs = append(attrs, &ldap.EntryAttribute{Name: "memberOf", Values: pi.GroupsForUser(u)})

			attrs = append(attrs, AKAttrsToLDAP(u.Attributes)...)

			dn := fmt.Sprintf("cn=%s,%s", *u.Username, pi.UserDN)
			entries = append(entries, &ldap.Entry{DN: dn, Attributes: attrs})
		}
	}
	pi.log.WithField("filter", searchReq.Filter).Debug("Search OK")
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
