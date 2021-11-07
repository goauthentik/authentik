package server

import (
	"github.com/go-openapi/strfmt"
	"github.com/nmcclain/ldap"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/flags"
)

type LDAPServerInstance interface {
	GetAPIClient() *api.APIClient
	GetOutpostName() string

	GetFlowSlug() string
	GetAppSlug() string
	GetSearchAllowedGroups() []*strfmt.UUID

	UserEntry(u api.User) *ldap.Entry

	GetBaseDN() string
	GetBaseGroupDN() string
	GetBaseUserDN() string

	GetUserDN(string) string
	GetGroupDN(string) string
	GetVirtualGroupDN(string) string

	GetUidNumber(api.User) string
	GetGidNumber(api.Group) string

	UsersForGroup(api.Group) []string

	GetFlags(string) (flags.UserFlags, bool)
	SetFlags(string, flags.UserFlags)
}
