package ldap

import (
	"context"
	"errors"
	"fmt"
	"net"
	"strings"

	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
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
			entries = append(entries, pi.GroupEntry(g))
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
	}

	if *u.IsActive {
        attrs = append(attrs, &ldap.EntryAttribute{Name: "accountStatus", Values: []string{"active"}})
	} else {
        attrs = append(attrs, &ldap.EntryAttribute{Name: "accountStatus", Values: []string{"inactive"}})
	}

	if u.IsSuperuser {
		attrs = append(attrs, &ldap.EntryAttribute{Name: "superuser", Values: []string{"active"}})
	} else {
        attrs = append(attrs, &ldap.EntryAttribute{Name: "superuser", Values: []string{"inactive"}})
	}

	attrs = append(attrs, &ldap.EntryAttribute{Name: "memberOf", Values: pi.GroupsForUser(u)})

	attrs = append(attrs, AKAttrsToLDAP(u.Attributes)...)

	dn := fmt.Sprintf("cn=%s,%s", u.Username, pi.UserDN)

	return &ldap.Entry{DN: dn, Attributes: attrs}
}

func (pi *ProviderInstance) GroupEntry(g api.Group) *ldap.Entry {
	attrs := []*ldap.EntryAttribute{
		{
			Name:   "cn",
			Values: []string{g.Name},
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
	return &ldap.Entry{DN: dn, Attributes: attrs}
}
