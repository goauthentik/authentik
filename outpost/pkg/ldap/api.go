package ldap

import (
	"errors"
	"fmt"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/pkg/client/outposts"
)

func (ls *LDAPServer) Refresh() error {
	outposts, err := ls.ac.Client.Outposts.OutpostsLdapList(outposts.NewOutpostsLdapListParams(), ls.ac.Auth)
	if err != nil {
		return err
	}
	if len(outposts.Payload.Results) < 1 {
		return errors.New("no ldap provider defined")
	}
	providers := make([]*ProviderInstance, len(outposts.Payload.Results))
	for idx, provider := range outposts.Payload.Results {
		userDN := strings.ToLower(fmt.Sprintf("cn=users,%s", provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("cn=groups,%s", provider.BaseDn))
		providers[idx] = &ProviderInstance{
			BaseDN:   provider.BaseDn,
			GroupDN:  groupDN,
			UserDN:   userDN,
			appSlug:  *provider.ApplicationSlug,
			flowSlug: *provider.BindFlowSlug,
			s:        ls,
			log:      log.WithField("provider", provider.Name),
		}
	}
	ls.providers = providers
	ls.log.Info("Update providers")
	return nil
}

func (ls *LDAPServer) Start() error {
	listen := "0.0.0.0:3389"
	log.Debugf("Listening on %s", listen)
	err := ls.s.ListenAndServe(listen)
	if err != nil {
		ls.log.Errorf("LDAP Server Failed: %s", err.Error())
		return err
	}
	return nil
}
