package proxyv2

import (
	"context"
	"crypto/tls"
	"errors"
	"net"
	"net/http"
	"strings"
	"sync"

	sentryhttp "github.com/getsentry/sentry-go/http"
	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	"go.uber.org/zap"
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
	log         *zap.Logger
	mux         *mux.Router
	akAPI       *ak.APIController
}

func NewProxyServer(ac *ak.APIController) *ProxyServer {
	l := config.Get().Logger().Named("authentik.outpost.proxyv2")
	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		l.Fatal("Failed to generate self-signed certificate", zap.Error(err))
	}

	rootMux := mux.NewRouter()
	rootMux.Use(func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
			h.ServeHTTP(rw, r)
			rw.Header().Set("X-Powered-By", "authentik_proxy2")
		})
	})

	globalMux := rootMux.NewRoute().Subrouter()
	globalMux.Use(web.NewLoggingHandler(l.Named("authentik.outpost.proxyv2.http"), nil))
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
	// Always handle requests for outpost paths that should answer regardless of hostname
	if strings.HasPrefix(r.URL.Path, "/outpost.goauthentik.io/ping") ||
		strings.HasPrefix(r.URL.Path, "/outpost.goauthentik.io/static") {
		ps.mux.ServeHTTP(rw, r)
		return true
	}
	// lookup app by hostname
	a, _ := ps.lookupApp(r)
	if a == nil {
		return false
	}
	// check if the app should handle this URL, or is setup in proxy mode
	if a.ShouldHandleURL(r) || a.Mode() == api.PROXYMODE_PROXY {
		ps.mux.ServeHTTP(rw, r)
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
		ps.log.Debug("failed to get certificate for ServerName", zap.String("server-name", serverName))
		return nil
	}
	if app.Cert == nil {
		ps.log.Debug("app does not have a certificate", zap.String("server-name", serverName))
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
		ps.log.Warn("Failed to listen", zap.Error(err))
		return
	}
	proxyListener := &proxyproto.Listener{Listener: listener, ConnPolicy: utils.GetProxyConnectionPolicy()}
	defer proxyListener.Close()

	ps.log.Info("Starting HTTP server", zap.String("listen", listenAddress))
	ps.serve(proxyListener)
	ps.log.Info("Stopping HTTP server", zap.String("listen", listenAddress))
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ps *ProxyServer) ServeHTTPS() {
	listenAddress := config.Get().Listen.HTTPS
	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetCertificate = ps.getCertificates

	ln, err := net.Listen("tcp", listenAddress)
	if err != nil {
		ps.log.Warn("Failed to listen (TLS)", zap.Error(err))
		return
	}
	proxyListener := &proxyproto.Listener{Listener: web.TCPKeepAliveListener{TCPListener: ln.(*net.TCPListener)}, ConnPolicy: utils.GetProxyConnectionPolicy()}
	defer proxyListener.Close()

	tlsListener := tls.NewListener(proxyListener, tlsConfig)
	ps.log.Info("Starting HTTPS server", zap.String("listen", listenAddress))
	ps.serve(tlsListener)
	ps.log.Info("Stopping HTTPS server", zap.String("listen", listenAddress))
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
			ps.log.Info("HTTP server Shutdown", zap.Error(err))
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ps.log.Error("Failed to serve", zap.Error(err))
	}
	<-idleConnsClosed
}
