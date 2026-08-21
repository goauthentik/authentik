package group

import (
	"strconv"

	"beryju.io/ldap"

	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/server"
	"goauthentik.io/internal/outpost/ldap/utils"
	api "goauthentik.io/packages/client-go"
)

type LDAPGroup struct {
	DN             string
	CN             string
	Uid            string
	GidNumber      string
	Member         []string
	MemberOf       []string
	IsSuperuser    bool
	IsVirtualGroup bool
	Attributes     map[string]any
}

func (lg *LDAPGroup) Entry() *ldap.Entry {
	attrs := utils.AttributesToLDAP(lg.Attributes, func(key string) string {
		return utils.AttributeKeySanitize(key)
	}, func(value []string) []string {
		return value
	})

	// RFC 4519 §3.5 / §3.6 define groupOfNames and groupOfUniqueNames with
	// member (resp. uniqueMember) as a MUST attribute, so an entry that
	// advertises those object classes without any members is schema-invalid
	// and breaks strict LDAP client libraries that validate incoming
	// attributes against the declared schema. Keep the authentik-specific
	// classes and posixGroup (neither of which requires `member`) on
	// member-less groups, and only add groupOfNames / groupOfUniqueNames
	// when we actually have members to publish.
	objectClass := []string{constants.OCGroup, constants.OCAKGroup, constants.OCPosixGroup}
	if len(lg.Member) > 0 {
		objectClass = append(objectClass, constants.OCGroupOfUniqueNames, constants.OCGroupOfNames)
	}
	if lg.IsVirtualGroup {
		objectClass = append(objectClass, constants.OCAKVirtualGroup)
	}

	attrs = utils.EnsureAttributes(attrs, map[string][]string{
		"ak-superuser":   {strconv.FormatBool(lg.IsSuperuser)},
		"objectClass":    objectClass,
		"member":         lg.Member,
		"memberOf":       lg.MemberOf,
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
		GidNumber:      si.GetGroupGidNumber(g),
		Member:         si.MembersForGroup(g),
		MemberOf:       si.MemberOfForGroup(g),
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
		GidNumber:      si.GetUserGidNumber(u),
		Member:         []string{si.GetUserDN(u.Username)},
		IsVirtualGroup: true,
		IsSuperuser:    false,
		Attributes:     nil,
	}
}
