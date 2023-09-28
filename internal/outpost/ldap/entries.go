package ldap

import (
	"fmt"
	"strconv"
	"strings"

	"beryju.io/ldap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/utils"
)

func (pi *ProviderInstance) UserEntry(u api.User) *ldap.Entry {
	dn := pi.GetUserDN(u.Username)
	attrs := utils.AttributesToLDAP(u.Attributes, func(key string) string {
		return utils.AttributeKeySanitize(key)
	}, func(value []string) []string {
		for i, v := range value {
			if strings.Contains(v, "%s") {
				value[i] = fmt.Sprintf(v, u.Username)
			}
		}
		return value
	})

	if u.IsActive == nil {
		u.IsActive = api.PtrBool(false)
	}
	if u.Email == nil {
		u.Email = api.PtrString("")
	}
	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		"ak-active":      {strconv.FormatBool(*u.IsActive)},
		"ak-superuser":   {strconv.FormatBool(u.IsSuperuser)},
		"memberOf":       pi.GroupsForUser(u),
		"cn":             {u.Username},
		"sAMAccountName": {u.Username},
		"uid":            {u.Uid},
		"name":           {u.Name},
		"displayName":    {u.Name},
		"mail":           {*u.Email},
		"objectClass": {
			constants.OCUser,
			constants.OCOrgPerson,
			constants.OCInetOrgPerson,
			constants.OCAKUser,
			constants.OCPosixAccount,
		},
		"uidNumber":     {pi.GetUidNumber(u)},
		"gidNumber":     {pi.GetUidNumber(u)},
		"homeDirectory": {fmt.Sprintf("/home/%s", u.Username)},
		"sn":            {u.Name},
	})
	return &ldap.Entry{DN: dn, Attributes: attrs}
}
