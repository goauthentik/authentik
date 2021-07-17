package ldap

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ak"
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
		logger := log.WithField("logger", "authentik.outpost.ldap").WithField("provider", provider.Name)
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
			tlsServerName:       provider.TlsServerName,
			uidStartNumber:      *provider.UidStartNumber,
			gidStartNumber:      *provider.GidStartNumber,
		}
		if provider.Certificate.Get() != nil {
			logger.WithField("provider", provider.Name).Debug("Enabling TLS")
			cert, err := ak.ParseCertificate(*provider.Certificate.Get(), ls.ac.Client.CryptoApi)
			if err != nil {
				logger.WithField("provider", provider.Name).WithError(err).Warning("Failed to fetch certificate")
			} else {
				providers[idx].cert = cert
				logger.WithField("provider", provider.Name).Debug("Loaded certificates")
			}
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

func (ls *LDAPServer) StartLDAPTLSServer() error {
	listen := "0.0.0.0:6636"
	tlsConfig := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ls.getCertificates,
	}

	ln, err := tls.Listen("tcp", listen, tlsConfig)
	if err != nil {
		ls.log.Fatalf("FATAL: listen (%s) failed - %s", listen, err)
	}
	ls.log.WithField("listen", listen).Info("Starting ldap tls server")
	err = ls.s.Serve(ln)
	if err != nil {
		return err
	}
	ls.log.Printf("closing %s", ln.Addr())
	return ls.s.ListenAndServe(listen)
}

func (ls *LDAPServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(3)
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
	go func() {
		defer wg.Done()
		err := ls.StartLDAPTLSServer()
		if err != nil {
			panic(err)
		}
	}()
	wg.Wait()
	return nil
}
