package ldap

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/nmcclain/ldap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/utils"
)

func (pi *ProviderInstance) UserEntry(u api.User) *ldap.Entry {
	dn := pi.GetUserDN(u.Username)
	userValueMap := func(value []string) []string {
		for i, v := range value {
			if strings.Contains(v, "%s") {
				value[i] = fmt.Sprintf(v, u.Username)
			}
		}
		return value
	}
	attrs := utils.AttributesToLDAP(u.Attributes, func(key string) string {
		return utils.AttributeKeySanitize(key)
	}, userValueMap)
	rawAttrs := utils.AttributesToLDAP(u.Attributes, func(key string) string {
		return key
	}, userValueMap)
	// Only append attributes that don't already exist
	// TODO: Remove in 2023.3
	for _, rawAttr := range rawAttrs {
		for _, attr := range attrs {
			if !strings.EqualFold(attr.Name, rawAttr.Name) {
				attrs = append(attrs, rawAttr)
			}
		}
	}

	if u.IsActive == nil {
		u.IsActive = api.PtrBool(false)
	}
	if u.Email == nil {
		u.Email = api.PtrString("")
	}
	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		// Old fields for backwards compatibility
		"goauthentik.io/ldap/active":    {strconv.FormatBool(*u.IsActive)},
		"goauthentik.io/ldap/superuser": {strconv.FormatBool(u.IsSuperuser)},
		// End old fields
		"ak-active":      {strconv.FormatBool(*u.IsActive)},
		"ak-superuser":   {strconv.FormatBool(u.IsSuperuser)},
		"memberOf":       pi.GroupsForUser(u),
		"cn":             {u.Username},
		"sAMAccountName": {u.Username},
		"uid":            {u.Uid},
		"name":           {u.Name},
		"displayName":    {u.Name},
		"mail":           {*u.Email},
		"objectClass":    {constants.OCUser, constants.OCOrgPerson, constants.OCInetOrgPerson, constants.OCAKUser},
		"uidNumber":      {pi.GetUidNumber(u)},
		"gidNumber":      {pi.GetUidNumber(u)},
		"homeDirectory":  {fmt.Sprintf("/home/%s", u.Username)},
		"sn":             {u.Name},
	})
	return &ldap.Entry{DN: dn, Attributes: attrs}
}
