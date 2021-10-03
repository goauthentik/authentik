package proxyv2

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/utils/web"
)

type ProxyServer struct {
	Listen     string
	PortOffset int

	defaultCert tls.Certificate
	stop        chan struct{} // channel for waiting shutdown

	cryptoStore *ak.CryptoStore
	apps        map[string]*application.Application
	log         *log.Entry
	mux         *mux.Router
	akAPI       *ak.APIController
}

func NewProxyServer(ac *ak.APIController, portOffset int) *ProxyServer {
	l := log.WithField("logger", "authentik.outpost.proxyv2")
	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		l.Fatal(err)
	}

	rootMux := mux.NewRouter()
	rootMux.Use(func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
			h.ServeHTTP(rw, r)
			rw.Header().Set("Server", "authentik_proxy2")
		})
	})

	globalMux := rootMux.NewRoute().Subrouter()
	globalMux.Use(web.NewLoggingHandler(l.WithField("logger", "authentik.outpost.proxyv2.http"), nil))
	s := &ProxyServer{
		Listen:     "0.0.0.0:%d",
		PortOffset: portOffset,

		cryptoStore: ak.NewCryptoStore(ac.Client.CryptoApi),
		apps:        make(map[string]*application.Application),
		log:         l,
		mux:         rootMux,
		akAPI:       ac,
		defaultCert: defaultCert,
	}
	globalMux.PathPrefix("/akprox/static").HandlerFunc(s.HandleStatic)
	rootMux.PathPrefix("/").HandlerFunc(s.Handle)
	return s
}

func (ps *ProxyServer) HandleHost(host string, rw http.ResponseWriter, r *http.Request) bool {
	if app, ok := ps.apps[host]; ok {
		if app.Mode() == api.PROXYMODE_PROXY {
			ps.log.WithField("host", host).Trace("routing to proxy outpost")
			app.ServeHTTP(rw, r)
			return true
		}
	}
	return false
}

func (ps *ProxyServer) Type() string {
	return "proxy"
}

func (ps *ProxyServer) TimerFlowCacheExpiry() {}

func (ps *ProxyServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	app, ok := ps.apps[info.ServerName]
	if !ok {
		ps.log.WithField("server-name", info.ServerName).Debug("app does not exist")
		return &ps.defaultCert, nil
	}
	if app.Cert == nil {
		ps.log.WithField("server-name", info.ServerName).Debug("app does not have a certificate")
		return &ps.defaultCert, nil
	}
	return app.Cert, nil
}

// ServeHTTP constructs a net.Listener and starts handling HTTP requests
func (ps *ProxyServer) ServeHTTP() {
	listenAddress := fmt.Sprintf(ps.Listen, 9000+ps.PortOffset)
	listener, err := net.Listen("tcp", listenAddress)
	if err != nil {
		ps.log.Fatalf("FATAL: listen (%s) failed - %s", listenAddress, err)
	}
	proxyListener := &proxyproto.Listener{Listener: listener}
	defer proxyListener.Close()

	ps.log.Printf("listening on %s", listener.Addr())
	ps.serve(proxyListener)
	ps.log.Printf("closing %s", listener.Addr())
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ps *ProxyServer) ServeHTTPS() {
	listenAddress := fmt.Sprintf(ps.Listen, 9443+ps.PortOffset)
	config := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ps.getCertificates,
	}

	ln, err := net.Listen("tcp", listenAddress)
	if err != nil {
		ps.log.Fatalf("listen (%s) failed - %s", listenAddress, err)
	}
	ps.log.Printf("listening on %s", ln.Addr())

	proxyListener := &proxyproto.Listener{Listener: tcpKeepAliveListener{ln.(*net.TCPListener)}}
	defer proxyListener.Close()

	tlsListener := tls.NewListener(proxyListener, config)
	ps.serve(tlsListener)
	ps.log.Printf("closing %s", tlsListener.Addr())
}

func (ps *ProxyServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(3)
	go func() {
		defer wg.Done()
		ps.log.Debug("Starting HTTP Server...")
		ps.ServeHTTP()
	}()
	go func() {
		defer wg.Done()
		ps.log.Debug("Starting HTTPs Server...")
		ps.ServeHTTPS()
	}()
	go func() {
		defer wg.Done()
		ps.log.Debug("Starting Metrics Server...")
		metrics.RunServer()
	}()
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
			ps.log.Printf("HTTP server Shutdown: %v", err)
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ps.log.Errorf("ERROR: http.Serve() - %s", err)
	}
	<-idleConnsClosed
}

// tcpKeepAliveListener sets TCP keep-alive timeouts on accepted
// connections. It's used by ListenAndServe and ListenAndServeTLS so
// dead TCP connections (e.g. closing laptop mid-download) eventually
// go away.
type tcpKeepAliveListener struct {
	*net.TCPListener
}

func (ln tcpKeepAliveListener) Accept() (net.Conn, error) {
	tc, err := ln.AcceptTCP()
	if err != nil {
		return nil, err
	}
	err = tc.SetKeepAlive(true)
	if err != nil {
		log.Printf("Error setting Keep-Alive: %v", err)
	}
	err = tc.SetKeepAlivePeriod(3 * time.Minute)
	if err != nil {
		log.Printf("Error setting Keep-Alive period: %v", err)
	}
	return tc, nil
}
