package ldap

import (
	"context"
	"crypto/tls"
	"net"
	"sync"

	"github.com/pires/go-proxyproto"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/utils"

	"beryju.io/ldap"
)

type LDAPServer struct {
	s           *ldap.Server
	log         *zap.Logger
	ac          *ak.APIController
	cs          *ak.CryptoStore
	defaultCert *tls.Certificate
	providers   []*ProviderInstance
}

func NewServer(ac *ak.APIController) *LDAPServer {
	ls := &LDAPServer{
		log:       config.Get().Logger().Named("authentik.outpost.ldap"),
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
		ls.log.Warn("failed to get self-signed certificate", zap.Error(err))
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
		ls.log.Warn("Failed to listen (SSL)", zap.String("listen", listen), zap.Error(err))
		return err
	}
	proxyListener := &proxyproto.Listener{Listener: ln, ConnPolicy: utils.GetProxyConnectionPolicy()}
	defer proxyListener.Close()

	ls.log.Info("Starting LDAP server", zap.String("listen", listen))
	err = ls.s.Serve(proxyListener)
	if err != nil {
		return err
	}
	ls.log.Info("Stopping LDAP server", zap.String("listen", listen))
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
		ls.log.Debug("Pre-heating flow cache", zap.String("flow", p.authenticationFlowSlug))
		p.binder.TimerFlowCacheExpiry(ctx)
	}
}
