package ldap

import (
	"fmt"

	"github.com/nmcclain/ldap"
	"goauthentik.io/outpost/api"
)

func BoolToString(in bool) string {
	if in {
		return "true"
	}
	return "false"
}

func AKAttrsToLDAP(attrs interface{}) []*ldap.EntryAttribute {
	attrList := []*ldap.EntryAttribute{}
	a := attrs.(*map[string]interface{})
	for attrKey, attrValue := range *a {
		entry := &ldap.EntryAttribute{Name: attrKey}
		switch t := attrValue.(type) {
		case []string:
			entry.Values = t
		case string:
			entry.Values = []string{t}
		case bool:
			entry.Values = []string{BoolToString(t)}
		}
		attrList = append(attrList, entry)
	}
	return attrList
}

func (pi *ProviderInstance) GroupsForUser(user api.User) []string {
	groups := make([]string, len(user.Groups))
	for i, group := range user.Groups {
		groups[i] = pi.GetGroupDN(group)
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

func (pi *ProviderInstance) GetUserDN(user string) string {
	return fmt.Sprintf("cn=%s,%s", user, pi.UserDN)
}

func (pi *ProviderInstance) GetGroupDN(group api.Group) string {
	return fmt.Sprintf("cn=%s,%s", group.Name, pi.GroupDN)
}
