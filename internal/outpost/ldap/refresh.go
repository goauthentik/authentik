package ldap

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ldap/bind"
	directbind "goauthentik.io/internal/outpost/ldap/bind/direct"
	memorybind "goauthentik.io/internal/outpost/ldap/bind/memory"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	directsearch "goauthentik.io/internal/outpost/ldap/search/direct"
	memorysearch "goauthentik.io/internal/outpost/ldap/search/memory"
)

func (ls *LDAPServer) getCurrentProvider(pk int32) *ProviderInstance {
	for _, p := range ls.providers {
		if p.providerPk == pk {
			return p
		}
	}
	return nil
}

func (ls *LDAPServer) Refresh() error {
	apiProviders, err := ak.Paginator(ls.ac.Client.OutpostsApi.OutpostsLdapList(context.Background()), ak.PaginatorOptions{
		PageSize: 100,
		Logger:   ls.log,
	})
	if err != nil {
		return err
	}
	if len(apiProviders) < 1 {
		return errors.New("no ldap provider defined")
	}
	providers := make([]*ProviderInstance, len(apiProviders))
	for idx, provider := range apiProviders {
		userDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUUsers, *provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUGroups, *provider.BaseDn))
		virtualGroupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", constants.OUVirtualGroups, *provider.BaseDn))
		logger := log.WithField("logger", "authentik.outpost.ldap").WithField("provider", provider.Name)

		// Get existing instance so we can transfer boundUsers
		existing := ls.getCurrentProvider(provider.Pk)
		usersMutex := &sync.RWMutex{}
		users := make(map[string]*flags.UserFlags)
		if existing != nil {
			usersMutex = existing.boundUsersMutex
			// Shallow copy, no need to lock
			users = existing.boundUsers
		}

		providers[idx] = &ProviderInstance{
			BaseDN:                 provider.GetBaseDn(),
			VirtualGroupDN:         virtualGroupDN,
			GroupDN:                groupDN,
			UserDN:                 userDN,
			appSlug:                provider.ApplicationSlug,
			authenticationFlowSlug: provider.BindFlowSlug,
			invalidationFlowSlug:   provider.UnbindFlowSlug.Get(),
			boundUsersMutex:        usersMutex,
			boundUsers:             users,
			s:                      ls,
			log:                    logger,
			tlsServerName:          provider.TlsServerName,
			uidStartNumber:         provider.GetUidStartNumber(),
			gidStartNumber:         provider.GetGidStartNumber(),
			mfaSupport:             provider.GetMfaSupport(),
			outpostName:            ls.ac.Outpost.Name,
			providerPk:             provider.Pk,
		}
		if kp := provider.Certificate.Get(); kp != nil {
			err := ls.cs.AddKeypair(*kp)
			if err != nil {
				ls.log.WithError(err).Warning("Failed to initially fetch certificate")
			}
			providers[idx].cert = ls.cs.Get(*kp)
			providers[idx].certUUID = *kp
		}
		if *provider.SearchMode.Ptr() == api.LDAPAPIACCESSMODE_CACHED {
			providers[idx].searcher = memorysearch.NewMemorySearcher(providers[idx])
		} else if *provider.SearchMode.Ptr() == api.LDAPAPIACCESSMODE_DIRECT {
			providers[idx].searcher = directsearch.NewDirectSearcher(providers[idx])
		}
		if *provider.BindMode.Ptr() == api.LDAPAPIACCESSMODE_CACHED {
			var oldBinder bind.Binder
			if existing != nil {
				oldBinder = existing.binder
			}
			providers[idx].binder = memorybind.NewSessionBinder(providers[idx], oldBinder)
		} else if *provider.BindMode.Ptr() == api.LDAPAPIACCESSMODE_DIRECT {
			providers[idx].binder = directbind.NewDirectBinder(providers[idx])
		}
	}
	ls.providers = providers
	ls.log.Info("Update providers")
	return nil
}
