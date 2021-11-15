package ldap

import (
	"fmt"
	"math/big"
	"strconv"
	"strings"

	"goauthentik.io/api"
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
	uidNumber, ok := user.GetAttributes()["uidNumber"].(string)

	if ok {
		return uidNumber
	}

	return strconv.FormatInt(int64(pi.uidStartNumber+user.Pk), 10)
}

func (pi *ProviderInstance) GetGidNumber(group api.Group) string {
	gidNumber, ok := group.GetAttributes()["gidNumber"].(string)

	if ok {
		return gidNumber
	}

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
