package ldap

import (
	"fmt"
	"strconv"

	"goauthentik.io/api/v3"
)

func (pi *ProviderInstance) GroupsForUser(user api.User) []string {
	groups := make([]string, len(user.Groups))
	for i, group := range user.GroupsObj {
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

func (pi *ProviderInstance) GetUserDN(user string) string {
	return fmt.Sprintf("cn=%s,%s", user, pi.UserDN)
}

func (pi *ProviderInstance) GetGroupDN(group string) string {
	return fmt.Sprintf("cn=%s,%s", group, pi.GroupDN)
}

func (pi *ProviderInstance) GetVirtualGroupDN(group string) string {
	return fmt.Sprintf("cn=%s,%s", group, pi.VirtualGroupDN)
}

func (pi *ProviderInstance) GetUidNumber(user api.User) string {
	uidNumber, ok := user.GetAttributes().(map[string]interface{})["uidNumber"].(string)

	if ok {
		return uidNumber
	}

	return strconv.FormatInt(int64(pi.uidStartNumber+user.Pk), 10)
}

func (pi *ProviderInstance) GetGidNumber(group api.Group) string {
	gidNumber, ok := group.GetAttributes().(map[string]interface{})["gidNumber"].(string)

	if ok {
		return gidNumber
	}

	return strconv.FormatInt(int64(pi.gidStartNumber+group.NumPk), 10)
}
