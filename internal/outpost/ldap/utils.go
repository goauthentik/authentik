package ldap

import (
	"fmt"
	"math/big"
	"reflect"
	"strconv"
	"strings"

	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
)

func BoolToString(in bool) string {
	if in {
		return "true"
	}
	return "false"
}

func ldapResolveTypeSingle(in interface{}) *string {
	switch t := in.(type) {
	case string:
		return &t
	case *string:
		return t
	case bool:
		s := BoolToString(t)
		return &s
	case *bool:
		s := BoolToString(*t)
		return &s
	default:
		log.WithField("type", reflect.TypeOf(in).String()).Warning("Type can't be mapped to LDAP yet")
		return nil
	}
}

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	a := attrs.(*map[string]interface{})
	for attrKey, attrValue := range *a {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = t
		case *[]string:
			entry.Values = *t
		case []interface{}:
			entry.Values = make([]string, len(t))
			for idx, v := range t {
				v := ldapResolveTypeSingle(v)
				entry.Values[idx] = *v
			}
		default:
			v := ldapResolveTypeSingle(t)
			if v != nil {
				entry.Values = []string{*v}
			}
		}
		attrList = append(attrList, entry)
	}
	return attrList
}

func (pi *ProviderInstance) GroupsForUser(user api.User) []string {
	groups := make([]string, len(user.Groups))
	for i, group := range user.Groups {
		groups[i] = pi.GetGroupDN(group.Name)
	}
	return groups
}

func (pi *ProviderInstance) UsersForGroup(group api.Group) []string {
	users := make([]string, len(group.UsersObj))
	for i, user := range group.UsersObj {
		users[i] = pi.GetUserDN(user.Username)
	}
	return users
}

func (pi *ProviderInstance) APIGroupToLDAPGroup(g api.Group) LDAPGroup {
	return LDAPGroup{
		dn:             pi.GetGroupDN(g.Name),
		cn:             g.Name,
		uid:            string(g.Pk),
		gidNumber:      pi.GetGidNumber(g),
		member:         pi.UsersForGroup(g),
		isVirtualGroup: false,
		isSuperuser:    *g.IsSuperuser,
		akAttributes:   g.Attributes,
	}
}

func (pi *ProviderInstance) APIUserToLDAPGroup(u api.User) LDAPGroup {
	return LDAPGroup{
		dn:             pi.GetGroupDN(u.Username),
		cn:             u.Username,
		uid:            u.Uid,
		gidNumber:      pi.GetUidNumber(u),
		member:         []string{pi.GetUserDN(u.Username)},
		isVirtualGroup: true,
		isSuperuser:    false,
		akAttributes:   nil,
	}
}

func (pi *ProviderInstance) GetUserDN(user string) string {
	return fmt.Sprintf("cn=%s,%s", user, pi.UserDN)
}

func (pi *ProviderInstance) GetGroupDN(group string) string {
	return fmt.Sprintf("cn=%s,%s", group, pi.GroupDN)
}

func (pi *ProviderInstance) GetUidNumber(user api.User) string {
	return strconv.FormatInt(int64(pi.uidStartNumber+user.Pk), 10)
}

func (pi *ProviderInstance) GetGidNumber(group api.Group) string {
	return strconv.FormatInt(int64(pi.gidStartNumber+pi.GetRIDForGroup(group.Pk)), 10)
}

func (pi *ProviderInstance) GetRIDForGroup(uid string) int32 {
	var i big.Int
	i.SetString(strings.Replace(uid, "-", "", -1), 16)
	intStr := i.String()

	// Get the last 5 characters/digits of the int-version of the UUID
	gid, err := strconv.Atoi(intStr[len(intStr)-5:])

	if err != nil {
		panic(err)
	}

	return int32(gid)
}
