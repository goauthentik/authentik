package ldap

import (
	"crypto/tls"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/search"
)

type ProviderInstance struct {
	BaseDN         string
	UserDN         string
	VirtualGroupDN string
	GroupDN        string

	searcher search.Searcher
	binder   bind.Binder

	appSlug  string
	flowSlug string
	s        *LDAPServer
	log      *log.Entry

	tlsServerName       *string
	cert                *tls.Certificate
	outpostName         string
	outpostPk           int32
	searchAllowedGroups []*strfmt.UUID
	boundUsersMutex     sync.RWMutex
	boundUsers          map[string]flags.UserFlags

	uidStartNumber int32
	gidStartNumber int32
}

func (pi *ProviderInstance) GetAPIClient() *api.APIClient {
	return pi.s.ac.Client
}

func (pi *ProviderInstance) GetBaseDN() string {
	return pi.BaseDN
}

func (pi *ProviderInstance) GetBaseGroupDN() string {
	return pi.GroupDN
}

func (pi *ProviderInstance) GetBaseUserDN() string {
	return pi.UserDN
}

func (pi *ProviderInstance) GetOutpostName() string {
	return pi.outpostName
}

func (pi *ProviderInstance) GetFlags(dn string) (flags.UserFlags, bool) {
	pi.boundUsersMutex.RLock()
	flags, ok := pi.boundUsers[dn]
	pi.boundUsersMutex.RUnlock()
	return flags, ok
}

func (pi *ProviderInstance) SetFlags(dn string, flag flags.UserFlags) {
	pi.boundUsersMutex.Lock()
	pi.boundUsers[dn] = flag
	pi.boundUsersMutex.Unlock()
}

func (pi *ProviderInstance) GetAppSlug() string {
	return pi.appSlug
}

func (pi *ProviderInstance) GetFlowSlug() string {
	return pi.flowSlug
}

func (pi *ProviderInstance) GetSearchAllowedGroups() []*strfmt.UUID {
	return pi.searchAllowedGroups
}
