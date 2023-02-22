package ldap

import (
	"strconv"

	"github.com/nmcclain/ldap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/utils"
)

func (pi *ProviderInstance) UserEntry(u api.User) *ldap.Entry {
	dn := pi.GetUserDN(u.Username)
	attrs := utils.AttributesToLDAP(u.Attributes, false)
	sanitizedAttrs := utils.AttributesToLDAP(u.Attributes, true)
	attrs = append(attrs, sanitizedAttrs...)

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
	})
	return &ldap.Entry{DN: dn, Attributes: attrs}
}
