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

func (ls *LDAPServer) StartHTTPServer() error {
	listen := "0.0.0.0:4180" // same port as proxy
	m := http.NewServeMux()
	m.HandleFunc("/akprox/ping", func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	ls.log.WithField("listen", listen).Info("Starting http server")
	return http.ListenAndServe(listen, m)
}

func (ls *LDAPServer) StartLDAPServer() error {
	listen := "0.0.0.0:3389"
	ls.log.WithField("listen", listen).Info("Starting ldap server")
	return ls.s.ListenAndServe(listen)
}

func (ls *LDAPServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		err := ls.StartHTTPServer()
		if err != nil {
			panic(err)
		}
	}()
	go func() {
		defer wg.Done()
		err := ls.StartLDAPServer()
		if err != nil {
			panic(err)
		}
	}()
	wg.Wait()
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
