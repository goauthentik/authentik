package ldap

import (
	"crypto/tls"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ldap/bind"
	ldapConstants "goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/utils"
)

type ProviderInstance struct {
	BaseDN         string
	UserDN         string
	VirtualGroupDN string
	GroupDN        string

	searcher search.Searcher
	binder   bind.Binder

	appSlug                string
	authenticationFlowSlug string
	invalidationFlowSlug   string
	s                      *LDAPServer
	log                    *log.Entry

	tlsServerName       *string
	cert                *tls.Certificate
	certUUID            string
	outpostName         string
	outpostPk           int32
	searchAllowedGroups []*strfmt.UUID
	boundUsersMutex     *sync.RWMutex
	boundUsers          map[string]*flags.UserFlags

	uidStartNumber int32
	gidStartNumber int32
	mfaSupport     bool
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

func (pi *ProviderInstance) GetBaseVirtualGroupDN() string {
	return pi.VirtualGroupDN
}

func (pi *ProviderInstance) GetBaseUserDN() string {
	return pi.UserDN
}

func (pi *ProviderInstance) GetOutpostName() string {
	return pi.outpostName
}

func (pi *ProviderInstance) GetMFASupport() bool {
	return pi.mfaSupport
}

func (pi *ProviderInstance) GetFlags(dn string) *flags.UserFlags {
	pi.boundUsersMutex.RLock()
	defer pi.boundUsersMutex.RUnlock()
	flags, ok := pi.boundUsers[dn]
	if !ok {
		return nil
	}
	return flags
}

func (pi *ProviderInstance) SetFlags(dn string, flag *flags.UserFlags) {
	pi.boundUsersMutex.Lock()
	if flag == nil {
		delete(pi.boundUsers, dn)
	} else {
		pi.boundUsers[dn] = flag
	}
	pi.boundUsersMutex.Unlock()
}

func (pi *ProviderInstance) GetAppSlug() string {
	return pi.appSlug
}

func (pi *ProviderInstance) GetAuthenticationFlowSlug() string {
	return pi.authenticationFlowSlug
}

func (pi *ProviderInstance) GetInvalidationFlowSlug() string {
	return pi.invalidationFlowSlug
}

func (pi *ProviderInstance) GetSearchAllowedGroups() []*strfmt.UUID {
	return pi.searchAllowedGroups
}

func (pi *ProviderInstance) GetNeededObjects(scope int, baseDN string, filterOC string) (bool, bool) {
	needUsers := false
	needGroups := false

	// We only want to load users/groups if we're actually going to be asked
	// for at least one user or group based on the search's base DN and scope.
	//
	// If our requested base DN doesn't match any of the container DNs, then
	// we're probably loading a user or group. If it does, then make sure our
	// scope will eventually take us to users or groups.
	if (strings.EqualFold(baseDN, pi.BaseDN) || utils.HasSuffixNoCase(baseDN, pi.UserDN)) && utils.IncludeObjectClass(filterOC, ldapConstants.GetUserOCs()) {
		if baseDN != pi.UserDN && baseDN != pi.BaseDN ||
			strings.EqualFold(baseDN, pi.BaseDN) && scope > 1 ||
			strings.EqualFold(baseDN, pi.UserDN) && scope > 0 {
			needUsers = true
		}
	}

	if (strings.EqualFold(baseDN, pi.BaseDN) || utils.HasSuffixNoCase(baseDN, pi.GroupDN)) && utils.IncludeObjectClass(filterOC, ldapConstants.GetGroupOCs()) {
		if baseDN != pi.GroupDN && baseDN != pi.BaseDN ||
			strings.EqualFold(baseDN, pi.BaseDN) && scope > 1 ||
			strings.EqualFold(baseDN, pi.GroupDN) && scope > 0 {
			needGroups = true
		}
	}

	if (strings.EqualFold(baseDN, pi.BaseDN) || utils.HasSuffixNoCase(baseDN, pi.VirtualGroupDN)) && utils.IncludeObjectClass(filterOC, ldapConstants.GetVirtualGroupOCs()) {
		if baseDN != pi.VirtualGroupDN && baseDN != pi.BaseDN ||
			strings.EqualFold(baseDN, pi.BaseDN) && scope > 1 ||
			strings.EqualFold(baseDN, pi.VirtualGroupDN) && scope > 0 {
			needUsers = true
		}
	}

	return needUsers, needGroups
}
