package ldap

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	directbind "goauthentik.io/internal/outpost/ldap/bind/direct"
	memorybind "goauthentik.io/internal/outpost/ldap/bind/memory"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	directsearch "goauthentik.io/internal/outpost/ldap/search/direct"
	memorysearch "goauthentik.io/internal/outpost/ldap/search/memory"
)

func (ls *LDAPServer) getCurrentProvider(pk int32) *ProviderInstance {
	for _, p := range ls.providers {
		if p.outpostPk == pk {
			return p
		}
	}
	return nil
}

func (ls *LDAPServer) Refresh() error {
	outposts, _, err := ls.ac.Client.OutpostsApi.OutpostsLdapList(context.Background()).Execute()
	if err != nil {
		return err
	}
	if len(outposts.Results) < 1 {
		return errors.New("no ldap provider defined")
	}
	providers := make([]*ProviderInstance, len(outposts.Results))
	for idx, provider := range outposts.Results {
		userDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUUsers, *provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUGroups, *provider.BaseDn))
		virtualGroupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUVirtualGroups, *provider.BaseDn))
		logger := log.WithField("logger", "authentik.outpost.ldap").WithField("provider", provider.Name)

		// Get existing instance so we can transfer boundUsers
		existing := ls.getCurrentProvider(provider.Pk)
		users := make(map[string]*flags.UserFlags)
		if existing != nil {
			existing.boundUsersMutex.RLock()
			users = existing.boundUsers
			existing.boundUsersMutex.RUnlock()
		}

		providers[idx] = &ProviderInstance{
			BaseDN:              *provider.BaseDn,
			VirtualGroupDN:      virtualGroupDN,
			GroupDN:             groupDN,
			UserDN:              userDN,
			appSlug:             provider.ApplicationSlug,
			flowSlug:            provider.BindFlowSlug,
			searchAllowedGroups: []*strfmt.UUID{(*strfmt.UUID)(provider.SearchGroup.Get())},
			boundUsersMutex:     sync.RWMutex{},
			boundUsers:          users,
			s:                   ls,
			log:                 logger,
			tlsServerName:       provider.TlsServerName,
			uidStartNumber:      *provider.UidStartNumber,
			gidStartNumber:      *provider.GidStartNumber,
			outpostName:         ls.ac.Outpost.Name,
			outpostPk:           provider.Pk,
		}
		if provider.Certificate.Get() != nil {
			kp := provider.Certificate.Get()
			err := ls.cs.AddKeypair(*kp)
			if err != nil {
				ls.log.WithError(err).Warning("Failed to initially fetch certificate")
			}
			providers[idx].cert = ls.cs.Get(*kp)
		}
		if *provider.SearchMode.Ptr() == api.LDAPAPIACCESSMODE_CACHED {
			providers[idx].searcher = memorysearch.NewMemorySearcher(providers[idx])
		} else if *provider.SearchMode.Ptr() == api.LDAPAPIACCESSMODE_DIRECT {
			providers[idx].searcher = directsearch.NewDirectSearcher(providers[idx])
		}
		if *provider.BindMode.Ptr() == api.LDAPAPIACCESSMODE_CACHED {
			providers[idx].binder = memorybind.NewSessionBinder(providers[idx])
		} else if *provider.BindMode.Ptr() == api.LDAPAPIACCESSMODE_DIRECT {
			providers[idx].binder = directbind.NewDirectBinder(providers[idx])
		}
	}
	ls.providers = providers
	ls.log.Info("Update providers")
	return nil
}
