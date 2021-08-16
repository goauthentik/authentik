package proxy

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/utils/web"
)

// Server represents an HTTP server
type Server struct {
	Handlers map[string]*providerBundle
	Listen   string

	stop        chan struct{} // channel for waiting shutdown
	logger      *log.Entry
	ak          *ak.APIController
	cs          *ak.CryptoStore
	defaultCert tls.Certificate
}

// NewServer initialise a new HTTP Server
func NewServer(ac *ak.APIController) *Server {
	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	return &Server{
		Handlers:    make(map[string]*providerBundle),
		Listen:      "0.0.0.0:%d",
		logger:      log.WithField("logger", "authentik.outpost.proxy-http-server"),
		defaultCert: defaultCert,
		ak:          ac,
		cs:          ak.NewCryptoStore(ac.Client.CryptoApi),
	}
}

// ServeHTTP constructs a net.Listener and starts handling HTTP requests
func (s *Server) ServeHTTP() {
	listenAddress := fmt.Sprintf(s.Listen, 4180)
	listener, err := net.Listen("tcp", listenAddress)
	if err != nil {
		s.logger.Fatalf("FATAL: listen (%s) failed - %s", listenAddress, err)
	}
	proxyListener := &proxyproto.Listener{Listener: listener}
	defer proxyListener.Close()

	s.logger.Printf("listening on %s", listener.Addr())
	s.serve(proxyListener)
	s.logger.Printf("closing %s", listener.Addr())
}

func (s *Server) Handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/akprox/ping" {
		w.WriteHeader(204)
		return
	}
	host := web.GetHost(r)
	handler, ok := s.Handlers[host]
	if !ok {
		// If we only have one handler, host name switching doesn't matter
		if len(s.Handlers) == 1 {
			for k := range s.Handlers {
				s.Handlers[k].ServeHTTP(w, r)
				return
			}
		}
		// Get a list of all host keys we know
		hostKeys := make([]string, 0, len(s.Handlers))
		for k := range s.Handlers {
			hostKeys = append(hostKeys, k)
		}
		s.logger.WithField("host", host).WithField("known-hosts", strings.Join(hostKeys, ",")).Debug("Host header does not match any we know of")
		w.WriteHeader(404)
		return
	}
	handler.ServeHTTP(w, r)
}

func (s *Server) serve(listener net.Listener) {
	srv := &http.Server{Handler: http.HandlerFunc(s.Handler)}

	// See https://golang.org/pkg/net/http/#Server.Shutdown
	idleConnsClosed := make(chan struct{})
	go func() {
		<-s.stop // wait notification for stopping server

		// We received an interrupt signal, shut down.
		if err := srv.Shutdown(context.Background()); err != nil {
			// Error from closing listeners, or context timeout:
			s.logger.Printf("HTTP server Shutdown: %v", err)
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		s.logger.Errorf("ERROR: http.Serve() - %s", err)
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
