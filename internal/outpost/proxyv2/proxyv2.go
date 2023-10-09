package proxyv2

import (
	"context"
	"crypto/tls"
	"errors"
	"net"
	"net/http"
	"sync"

	sentryhttp "github.com/getsentry/sentry-go/http"
	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/utils"
	sentryutils "goauthentik.io/internal/utils/sentry"
	"goauthentik.io/internal/utils/web"
)

type ProxyServer struct {
	defaultCert tls.Certificate
	stop        chan struct{} // channel for waiting shutdown

	cryptoStore *ak.CryptoStore
	apps        map[string]*application.Application
	log         *log.Entry
	mux         *mux.Router
	akAPI       *ak.APIController
}

func NewProxyServer(ac *ak.APIController) *ProxyServer {
	l := log.WithField("logger", "authentik.outpost.proxyv2")
	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		l.Fatal(err)
	}

	rootMux := mux.NewRouter()
	rootMux.Use(func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
			h.ServeHTTP(rw, r)
			rw.Header().Set("X-Powered-By", "authentik_proxy2")
		})
	})

	globalMux := rootMux.NewRoute().Subrouter()
	globalMux.Use(web.NewLoggingHandler(l.WithField("logger", "authentik.outpost.proxyv2.http"), nil))
	if ac.GlobalConfig.ErrorReporting.Enabled {
		globalMux.Use(sentryhttp.New(sentryhttp.Options{}).Handle)
	}
	s := &ProxyServer{
		cryptoStore: ak.NewCryptoStore(ac.Client.CryptoApi),
		apps:        make(map[string]*application.Application),
		log:         l,
		mux:         rootMux,
		akAPI:       ac,
		defaultCert: defaultCert,
	}
	globalMux.PathPrefix("/outpost.goauthentik.io/static").HandlerFunc(s.HandleStatic)
	globalMux.Path("/outpost.goauthentik.io/ping").HandlerFunc(sentryutils.SentryNoSample(s.HandlePing))
	rootMux.PathPrefix("/").HandlerFunc(s.Handle)
	ac.AddWSHandler(s.handleWSMessage)
	return s
}

func (ps *ProxyServer) HandleHost(rw http.ResponseWriter, r *http.Request) bool {
	a, _ := ps.lookupApp(r)
	if a == nil {
		return false
	}
	if a.HasQuerySignature(r) || a.Mode() == api.PROXYMODE_PROXY {
		a.ServeHTTP(rw, r)
		return true
	}
	return false
}

func (ps *ProxyServer) Type() string {
	return "proxy"
}

func (ps *ProxyServer) TimerFlowCacheExpiry(context.Context) {}

func (ps *ProxyServer) GetCertificate(serverName string) *tls.Certificate {
	app, ok := ps.apps[serverName]
	if !ok {
		ps.log.WithField("server-name", serverName).Debug("failed to get certificate for ServerName")
		return nil
	}
	if app.Cert == nil {
		ps.log.WithField("server-name", serverName).Debug("app does not have a certificate")
		return nil
	}
	return app.Cert
}

func (ps *ProxyServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	sn := info.ServerName
	if sn == "" {
		return &ps.defaultCert, nil
	}
	appCert := ps.GetCertificate(sn)
	if appCert == nil {
		return &ps.defaultCert, nil
	}
	return appCert, nil
}

// ServeHTTP constructs a net.Listener and starts handling HTTP requests
func (ps *ProxyServer) ServeHTTP() {
	listenAddress := config.Get().Listen.HTTP
	listener, err := net.Listen("tcp", listenAddress)
	if err != nil {
		ps.log.WithField("listen", listenAddress).WithError(err).Warning("Failed to listen")
		return
	}
	proxyListener := &proxyproto.Listener{Listener: listener}
	defer proxyListener.Close()

	ps.log.WithField("listen", listenAddress).Info("Starting HTTP server")
	ps.serve(proxyListener)
	ps.log.WithField("listen", listenAddress).Info("Stopping HTTP server")
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ps *ProxyServer) ServeHTTPS() {
	listenAddress := config.Get().Listen.HTTPS
	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetCertificate = ps.getCertificates

	ln, err := net.Listen("tcp", listenAddress)
	if err != nil {
		ps.log.WithError(err).Warning("Failed to listen (TLS)")
		return
	}
	proxyListener := &proxyproto.Listener{Listener: web.TCPKeepAliveListener{TCPListener: ln.(*net.TCPListener)}}
	defer proxyListener.Close()

	tlsListener := tls.NewListener(proxyListener, tlsConfig)
	ps.log.WithField("listen", listenAddress).Info("Starting HTTPS server")
	ps.serve(tlsListener)
	ps.log.WithField("listen", listenAddress).Info("Stopping HTTPS server")
}

func (ps *ProxyServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(3)
	go func() {
		defer wg.Done()
		ps.ServeHTTP()
	}()
	go func() {
		defer wg.Done()
		ps.ServeHTTPS()
	}()
	go func() {
		defer wg.Done()
		metrics.RunServer()
	}()
	return nil
}

func (ps *ProxyServer) Stop() error {
	return nil
}

func (ps *ProxyServer) serve(listener net.Listener) {
	srv := &http.Server{Handler: ps.mux}

	// See https://golang.org/pkg/net/http/#Server.Shutdown
	idleConnsClosed := make(chan struct{})
	go func() {
		<-ps.stop // wait notification for stopping server

		// We received an interrupt signal, shut down.
		if err := srv.Shutdown(context.Background()); err != nil {
			// Error from closing listeners, or context timeout:
			ps.log.WithError(err).Info("HTTP server Shutdown")
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ps.log.Errorf("ERROR: http.Serve() - %s", err)
	}
	<-idleConnsClosed
}
