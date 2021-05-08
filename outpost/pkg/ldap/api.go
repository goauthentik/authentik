package ldap

import (
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
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
		userDN := strings.ToLower(fmt.Sprintf("ou=users,%s", provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("ou=groups,%s", provider.BaseDn))
		providers[idx] = &ProviderInstance{
			BaseDN:              provider.BaseDn,
			GroupDN:             groupDN,
			UserDN:              userDN,
			appSlug:             *provider.ApplicationSlug,
			flowSlug:            *provider.BindFlowSlug,
			searchAllowedGroups: []*strfmt.UUID{provider.SearchGroup},
			boundUsersMutex:     sync.RWMutex{},
			boundUsers:          make(map[string]UserFlags),
			s:                   ls,
			log:                 log.WithField("logger", "authentik.outpost.ldap").WithField("provider", provider.Name),
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

type transport struct {
	headers map[string]string
}

func (t *transport) RoundTrip(req *http.Request) (*http.Response, error) {
	for key, value := range t.headers {
		req.Header.Add(key, value)
	}
	return http.DefaultTransport.RoundTrip(req)
}
func newTransport(headers map[string]string) *transport {
	return &transport{headers}
}
