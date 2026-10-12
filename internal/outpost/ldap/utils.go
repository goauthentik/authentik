package ldap

import (
	"fmt"
	"strconv"

	api "goauthentik.io/packages/client-go"
)

func getAttributeString(attributes map[string]any, key string) (string, bool) {
	val, ok := attributes[key]
	if !ok || val == nil {
		return "", false
	}

	switch v := val.(type) {
	case string:
		return v, true
	case float64:
		return strconv.FormatFloat(v, 'f', -1, 64), true
	default:
		return "", false
	}
}

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
	uidNumber, ok := getAttributeString(user.GetAttributes(), "uidNumber")

	if ok {
		return uidNumber
	}

	return strconv.FormatInt(int64(pi.uidStartNumber+user.Pk), 10)
}

func (pi *ProviderInstance) GetUserGidNumber(user api.User) string {
	gidNumber, ok := getAttributeString(user.GetAttributes(), "gidNumber")

	if ok {
		return gidNumber
	}

	return pi.GetUserUidNumber(user)
}

func (pi *ProviderInstance) GetGroupGidNumber(group api.Group) string {
	gidNumber, ok := getAttributeString(group.GetAttributes(), "gidNumber")

	if ok {
		return gidNumber
	}

	return strconv.FormatInt(int64(pi.gidStartNumber+group.NumPk), 10)
}
