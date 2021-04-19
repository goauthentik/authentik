package ldap

import (
	"fmt"
	"net"
	"strconv"
	"strings"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/pkg/client/core"
)

func (ls *LDAPServer) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	bindDN = strings.ToLower(bindDN)
	baseDN := strings.ToLower("," + ls.BaseDN)

	entries := []*ldap.Entry{}
	filterEntity, err := ldap.GetFilterObjectClass(searchReq.Filter)
	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: error parsing filter: %s", searchReq.Filter)
	}
	if len(bindDN) < 1 {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: Anonymous BindDN not allowed %s", bindDN)
	}
	if !strings.HasSuffix(bindDN, baseDN) {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultInsufficientAccessRights}, fmt.Errorf("Search Error: BindDN %s not in our BaseDN %s", bindDN, ls.BaseDN)
	}

	switch filterEntity {
	default:
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("Search Error: unhandled filter type: %s [%s]", filterEntity, searchReq.Filter)
	case GroupObjectClass:
		groups, err := ls.ac.Client.Core.CoreGroupsList(core.NewCoreGroupsListParams(), ls.ac.Auth)
		if err != nil {
			return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, fmt.Errorf("API Error: %s", err)
		}
		for _, g := range groups.Payload.Results {
			attrs := []*ldap.EntryAttribute{
				{
					Name:   "cn",
					Values: []string{*g.Name},
				},
				{
					Name:   "uid",
					Values: []string{strconv.Itoa(int(g.Pk))},
				},
				{
					Name:   "objectClass",
					Values: []string{GroupObjectClass, "goauthentik.io/ldap/group"},
				},
			}
			attrs = append(attrs, AKAttrsToLDAP(g.Attributes)...)
			// attrs = append(attrs, &ldap.EntryAttribute{Name: "description", Values: []string{fmt.Sprintf("%s", g.Name)}})
			// attrs = append(attrs, &ldap.EntryAttribute{Name: "gidNumber", Values: []string{fmt.Sprintf("%d", g.UnixID)}})
			// attrs = append(attrs, &ldap.EntryAttribute{Name: "uniqueMember", Values: h.getGroupMembers(g.UnixID)})
			// attrs = append(attrs, &ldap.EntryAttribute{Name: "memberUid", Values: h.getGroupMemberIDs(g.UnixID)})
			dn := fmt.Sprintf("cn=%s,%s", *g.Name, ls.groupDN)
			entries = append(entries, &ldap.Entry{DN: dn, Attributes: attrs})
		}
	case UserObjectClass, "":
		users, err := ls.ac.Client.Core.CoreUsersList(core.NewCoreUsersListParams(), ls.ac.Auth)
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
					Values: []string{strconv.Itoa(int(u.Pk))},
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

			// attrs = append(attrs, &ldap.EntryAttribute{Name: "memberOf", Values: h.getGroupDNs(append(u.OtherGroups, u.PrimaryGroup))})

			attrs = append(attrs, AKAttrsToLDAP(u.Attributes)...)

			dn := fmt.Sprintf("cn=%s,%s", *u.Name, ls.userDN)
			entries = append(entries, &ldap.Entry{DN: dn, Attributes: attrs})
		}
	}
	ls.log.Debug(fmt.Sprintf("AP: Search OK: %s", searchReq.Filter))
	return ldap.ServerSearchResult{Entries: entries, Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess}, nil
}
