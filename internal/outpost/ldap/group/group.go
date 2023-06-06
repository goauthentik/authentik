package group

import (
	"strconv"

	"beryju.io/ldap"
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
	Attributes     map[string]interface{}
}

func (lg *LDAPGroup) Entry() *ldap.Entry {
	attrs := utils.AttributesToLDAP(lg.Attributes, func(key string) string {
		return utils.AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})

	objectClass := []string{constants.OCGroup, constants.OCGroupOfUniqueNames, constants.OCGroupOfNames, constants.OCAKGroup, constants.OCPosixGroup}
	if lg.IsVirtualGroup {
		objectClass = append(objectClass, constants.OCAKVirtualGroup)
	}

	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		"ak-superuser":   {strconv.FormatBool(lg.IsSuperuser)},
		"objectClass":    objectClass,
		"member":         lg.Member,
		"cn":             {lg.CN},
		"uid":            {lg.Uid},
		"sAMAccountName": {lg.CN},
		"gidNumber":      {lg.GidNumber},
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
		Attributes:     g.Attributes,
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
		Attributes:     nil,
	}
}
