package ldap

import (
	"context"
	"crypto/tls"
	"net"
	"sync"

	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/utils"

	"beryju.io/ldap"
)

type LDAPServer struct {
	s           *ldap.Server
	log         *log.Entry
	ac          *ak.APIController
	cs          *ak.CryptoStore
	defaultCert *tls.Certificate
	providers   []*ProviderInstance
}

func NewServer(ac *ak.APIController) *LDAPServer {
	ls := &LDAPServer{
		log:       log.WithField("logger", "authentik.outpost.ldap"),
		ac:        ac,
		cs:        ak.NewCryptoStore(ac.Client.CryptoApi),
		providers: []*ProviderInstance{},
	}
	s := ldap.NewServer()
	s.EnforceLDAP = true

	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetCertificate = ls.getCertificates
	s.StartTLS = tlsConfig

	ls.s = s

	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	ls.defaultCert = &defaultCert
	s.BindFunc("", ls)
	s.UnbindFunc("", ls)
	s.SearchFunc("", ls)
	return ls
}

func (ls *LDAPServer) Type() string {
	return "ldap"
}

func (ls *LDAPServer) StartLDAPServer() error {
	listen := config.Get().Listen.LDAP

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.WithField("listen", listen).WithError(err).Warning("Failed to listen (SSL)")
		return err
	}
	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	ls.log.WithField("listen", listen).Info("Starting LDAP server")
	err = ls.s.Serve(proxyListener)
	if err != nil {
		return err
	}
	ls.log.WithField("listen", listen).Info("Stopping LDAP server")
	return nil
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

func (ls *LDAPServer) Stop() error {
	return nil
}

func (ls *LDAPServer) TimerFlowCacheExpiry(ctx context.Context) {
	for _, p := range ls.providers {
		ls.log.WithField("flow", p.authenticationFlowSlug).Debug("Pre-heating flow cache")
		p.binder.TimerFlowCacheExpiry(ctx)
	}
}
