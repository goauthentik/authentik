package server

import (
	"beryju.io/ldap"
	"github.com/go-openapi/strfmt"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/flags"
)

type LDAPServerInstance interface {
	GetAPIClient() *api.APIClient
	GetOutpostName() string

	GetAuthenticationFlowSlug() string
	GetInvalidationFlowSlug() string
	GetAppSlug() string
	GetSearchAllowedGroups() []*strfmt.UUID

	UserEntry(u api.User) *ldap.Entry

	GetBaseDN() string
	GetBaseGroupDN() string
	GetBaseVirtualGroupDN() string
	GetBaseUserDN() string

	GetUserDN(string) string
	GetGroupDN(string) string
	GetVirtualGroupDN(string) string

	GetUidNumber(api.User) string
	GetGidNumber(api.Group) string

	UsersForGroup(api.Group) []string

	GetFlags(dn string) *flags.UserFlags
	SetFlags(dn string, flags *flags.UserFlags)

	GetNeededObjects(scope int, baseDN string, filterOC string) (bool, bool)
}
