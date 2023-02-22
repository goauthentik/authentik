package group

import (
	"strconv"
	"strings"

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
	Attributes     map[string]interface{}
}

func (lg *LDAPGroup) Entry() *ldap.Entry {
	attrs := utils.AttributesToLDAP(lg.Attributes, func(key string) string {
		return utils.AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})
	rawAttrs := utils.AttributesToLDAP(lg.Attributes, func(key string) string {
		return key
	}, func(value []string) []string {
		return value
	})
	// Only append attributes that don't already exist
	// TODO: Remove in 2023.3
	for _, rawAttr := range rawAttrs {
		for _, attr := range attrs {
			if !strings.EqualFold(attr.Name, rawAttr.Name) {
				attrs = append(attrs, rawAttr)
			}
		}
	}

	objectClass := []string{constants.OCGroup, constants.OCGroupOfUniqueNames, constants.OCGroupOfNames, constants.OCAKGroup, constants.OCPosixGroup}
	if lg.IsVirtualGroup {
		objectClass = append(objectClass, constants.OCAKVirtualGroup)
	}

	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		// Old fields for backwards compatibility
		"goauthentik.io/ldap/superuser": {strconv.FormatBool(lg.IsSuperuser)},
		// End old fields
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
