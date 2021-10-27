package ldap

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	directbind "goauthentik.io/internal/outpost/ldap/bind/direct"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/flags"
	memorysearch "goauthentik.io/internal/outpost/ldap/search/memory"
)

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
		providers[idx] = &ProviderInstance{
			BaseDN:              *provider.BaseDn,
			VirtualGroupDN:      virtualGroupDN,
			GroupDN:             groupDN,
			UserDN:              userDN,
			appSlug:             provider.ApplicationSlug,
			flowSlug:            provider.BindFlowSlug,
			searchAllowedGroups: []*strfmt.UUID{(*strfmt.UUID)(provider.SearchGroup.Get())},
			boundUsersMutex:     sync.RWMutex{},
			boundUsers:          make(map[string]flags.UserFlags),
			s:                   ls,
			log:                 logger,
			tlsServerName:       provider.TlsServerName,
			uidStartNumber:      *provider.UidStartNumber,
			gidStartNumber:      *provider.GidStartNumber,
			outpostName:         ls.ac.Outpost.Name,
		}
		if provider.Certificate.Get() != nil {
			kp := provider.Certificate.Get()
			err := ls.cs.AddKeypair(*kp)
			if err != nil {
				ls.log.WithError(err).Warning("Failed to initially fetch certificate")
			}
			providers[idx].cert = ls.cs.Get(*kp)
		}

		// providers[idx].searcher = directsearch.NewDirectSearcher(providers[idx])
		providers[idx].searcher = memorysearch.NewMemorySearcher(providers[idx])
		providers[idx].binder = directbind.NewDirectBinder(providers[idx])
	}
	ls.providers = providers
	ls.log.Info("Update providers")
	return nil
}
