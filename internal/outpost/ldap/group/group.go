package group

import (
	"github.com/nmcclain/ldap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
)

type LDAPGroup struct {
	DN             string
	CN             string
	Uid            string
	GidNumber      string
	Member         []string
	IsSuperuser    bool
	IsVirtualGroup bool
	AKAttributes   map[string]interface{}
}

func (lg *LDAPGroup) Entry() *ldap.Entry {
	attrs := utils.AKAttrsToLDAP(lg.AKAttributes)

	objectClass := []string{constants.OCGroup, constants.OCGroupOfUniqueNames, constants.OCGroupOfNames, constants.OCAKGroup}
	if lg.IsVirtualGroup {
		objectClass = append(objectClass, constants.OCAKVirtualGroup)
	}

	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		"objectClass":                   objectClass,
		"member":                        lg.Member,
		"goauthentik.io/ldap/superuser": {utils.BoolToString(lg.IsSuperuser)},
		"cn":                            {lg.CN},
		"uid":                           {lg.Uid},
		"sAMAccountName":                {lg.CN},
		"gidNumber":                     {lg.GidNumber},
	})
	return &ldap.Entry{DN: lg.DN, Attributes: attrs}
}

func FromAPIGroup(g api.Group, si server.LDAPServerInstance) *LDAPGroup {
	return &LDAPGroup{
		DN:             si.GetGroupDN(g.Name),
		CN:             g.Name,
		Uid:            string(g.Pk),
		GidNumber:      si.GetGidNumber(g),
		Member:         si.UsersForGroup(g),
		IsVirtualGroup: false,
		IsSuperuser:    *g.IsSuperuser,
		AKAttributes:   g.Attributes,
	}
}

func FromAPIUser(u api.User, si server.LDAPServerInstance) *LDAPGroup {
	return &LDAPGroup{
		DN:             si.GetVirtualGroupDN(u.Username),
		CN:             u.Username,
		Uid:            u.Uid,
		GidNumber:      si.GetUidNumber(u),
		Member:         []string{si.GetUserDN(u.Username)},
		IsVirtualGroup: true,
		IsSuperuser:    false,
		AKAttributes:   nil,
	}
}
