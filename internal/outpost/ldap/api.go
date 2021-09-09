package ldap

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"strings"
	"sync"

	"github.com/go-openapi/strfmt"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/metrics"
)

const (
	UsersOU         = "users"
	GroupsOU        = "groups"
	VirtualGroupsOU = "virtual-groups"
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
		userDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", UsersOU, *provider.BaseDn))
		groupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", GroupsOU, *provider.BaseDn))
		virtualGroupDN := strings.ToLower(fmt.Sprintf("ou=%s,%s", VirtualGroupsOU, *provider.BaseDn))
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
			boundUsers:          make(map[string]UserFlags),
			s:                   ls,
			log:                 logger,
			tlsServerName:       provider.TlsServerName,
			uidStartNumber:      *provider.UidStartNumber,
			gidStartNumber:      *provider.GidStartNumber,
		}
		if provider.Certificate.Get() != nil {
			kp := provider.Certificate.Get()
			err := ls.cs.AddKeypair(*kp)
			if err != nil {
				ls.log.WithError(err).Warning("Failed to initially fetch certificate")
			}
			providers[idx].cert = ls.cs.Get(*kp)
		}
	}
	ls.providers = providers
	ls.log.Info("Update providers")
	return nil
}

func (ls *LDAPServer) StartLDAPServer() error {
	listen := "0.0.0.0:3389"

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.Fatalf("FATAL: listen (%s) failed - %s", listen, err)
	}
	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	ls.log.WithField("listen", listen).Info("Starting ldap server")
	err = ls.s.Serve(proxyListener)
	if err != nil {
		return err
	}
	ls.log.Printf("closing %s", ln.Addr())
	return ls.s.ListenAndServe(listen)
}

func (ls *LDAPServer) StartLDAPTLSServer() error {
	listen := "0.0.0.0:6636"
	tlsConfig := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ls.getCertificates,
	}

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.Fatalf("FATAL: listen (%s) failed - %s", listen, err)
	}

	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	tln := tls.NewListener(proxyListener, tlsConfig)

	ls.log.WithField("listen", listen).Info("Starting ldap tls server")
	err = ls.s.Serve(tln)
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
		metrics.RunServer()
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
