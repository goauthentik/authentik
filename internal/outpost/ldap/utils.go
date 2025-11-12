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

func (pi *ProviderInstance) MembersForGroup(group api.Group) []string {
	users := make([]string, len(group.UsersObj))
	for i, user := range group.UsersObj {
		users[i] = pi.GetUserDN(user.Username)
	}
	children := make([]string, len(group.ChildrenObj))
	for i, child := range group.ChildrenObj {
		children[i] = pi.GetGroupDN(child.Name)
	}
	return append(users, children...)
}

func (pi *ProviderInstance) MemberOfForGroup(group api.Group) []string {
	groups := make([]string, len(group.ParentsObj))
	for i, group := range group.ParentsObj {
		fmt.Printf("in range")
		groups[i] = pi.GetGroupDN(group.Name)
	}
	return groups
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

func (pi *ProviderInstance) GetUserUidNumber(user api.User) string {
	uidNumber, ok := user.GetAttributes()["uidNumber"].(string)

	if ok {
		return uidNumber
	}

	return strconv.FormatInt(int64(pi.uidStartNumber+user.Pk), 10)
}

func (pi *ProviderInstance) GetUserGidNumber(user api.User) string {
	gidNumber, ok := user.GetAttributes()["gidNumber"].(string)

	if ok {
		return gidNumber
	}

	return pi.GetUserUidNumber(user)
}

func (pi *ProviderInstance) GetGroupGidNumber(group api.Group) string {
	gidNumber, ok := group.GetAttributes()["gidNumber"].(string)

	if ok {
		return gidNumber
	}

	return strconv.FormatInt(int64(pi.gidStartNumber+group.NumPk), 10)
}
