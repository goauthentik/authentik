package ldap

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
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
		userDN := strings.ToLower(fmt.Sprintf("ou=users,%s", *provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("ou=groups,%s", *provider.BaseDn))
		providers[idx] = &ProviderInstance{
			BaseDN:              *provider.BaseDn,
			GroupDN:             groupDN,
			UserDN:              userDN,
			appSlug:             provider.ApplicationSlug,
			flowSlug:            provider.BindFlowSlug,
			searchAllowedGroups: []*strfmt.UUID{(*strfmt.UUID)(provider.SearchGroup.Get())},
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
	inner   http.RoundTripper
}

func (t *transport) RoundTrip(req *http.Request) (*http.Response, error) {
	for key, value := range t.headers {
		req.Header.Add(key, value)
	}
	return t.inner.RoundTrip(req)
}
func newTransport(inner http.RoundTripper, headers map[string]string) *transport {
	return &transport{
		inner:   inner,
		headers: headers,
	}
}
