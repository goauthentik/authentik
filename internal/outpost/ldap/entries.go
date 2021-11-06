package ldap

import (
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/utils"
)

func (pi *ProviderInstance) UserEntry(u api.User) *ldap.Entry {
	dn := pi.GetUserDN(u.Username)
	attrs := utils.AKAttrsToLDAP(u.Attributes)

	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		"memberOf": pi.GroupsForUser(u),
		// Old fields for backwards compatibility
		"accountStatus": {utils.BoolToString(*u.IsActive)},
		"superuser":     {utils.BoolToString(u.IsSuperuser)},
		// End old fields
		"goauthentik.io/ldap/active":    {utils.BoolToString(*u.IsActive)},
		"goauthentik.io/ldap/superuser": {utils.BoolToString(u.IsSuperuser)},
		"cn":                            {u.Username},
		"sAMAccountName":                {u.Username},
		"uid":                           {u.Uid},
		"name":                          {u.Name},
		"displayName":                   {u.Name},
		"mail":                          {*u.Email},
		"objectClass":                   {constants.OCUser, constants.OCOrgPerson, constants.OCInetOrgPerson, constants.OCAKUser},
		"uidNumber":                     {pi.GetUidNumber(u)},
		"gidNumber":                     {pi.GetUidNumber(u)},
	})
	return &ldap.Entry{DN: dn, Attributes: attrs}
}
