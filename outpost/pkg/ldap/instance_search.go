package ldap

import (
	"context"
	"errors"
	"fmt"
	"net"
	"strings"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/api"
)

func (pi *ProviderInstance) SearchMe(user api.User, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	entries := make([]*ldap.Entry, 1)
	entries[0] = pi.UserEntry(user)
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}

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
	if !ok {
		pi.log.Debug("User info not cached")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, errors.New("access denied")
	}
	if !flags.CanSearch {
		pi.log.Debug("User can't search, showing info about user")
		return pi.SearchMe(flags.UserInfo, searchReq, conn)
	}

	switch filterEntity {
	default:
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, searchReq.Filter)
	case GroupObjectClass:
		groups, _, err := pi.s.ac.Client.CoreApi.CoreGroupsList(context.Background()).Execute()
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		pi.log.WithField("count", len(groups.Results)).Trace("Got results from API")

		for _, g := range groups.Results {
			entries = append(entries, pi.GroupEntry(pi.APIGroupToLDAPGroup(g)))
		}

		users, _, err := pi.s.ac.Client.CoreApi.CoreUsersList(context.Background()).Execute()
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}

		for _, u := range users.Results {
			entries = append(entries, pi.GroupEntry(pi.APIUserToLDAPGroup(u)))
		}
	case UserObjectClass, "":
		users, _, err := pi.s.ac.Client.CoreApi.CoreUsersList(context.Background()).Execute()
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		for _, u := range users.Results {
			entries = append(entries, pi.UserEntry(u))
		}
	}
	pi.log.WithField("filter", searchReq.Filter).Debug("Search OK")
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
