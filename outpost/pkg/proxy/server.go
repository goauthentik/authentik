package proxy

import (
	"context"
	"crypto/tls"
	"errors"
	"net"
	"net/http"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/pkg/ak"
)

// Server represents an HTTP server
type Server struct {
	Handlers map[string]*providerBundle

	stop        chan struct{} // channel for waiting shutdown
	logger      *log.Entry
	ak          *ak.APIController
	defaultCert tls.Certificate
}

// NewServer initialise a new HTTP Server
func NewServer(ac *ak.APIController) *Server {
	defaultCert, err := ak.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	return &Server{
		Handlers:    make(map[string]*providerBundle),
		logger:      log.WithField("component", "proxy-http-server"),
		defaultCert: defaultCert,
		ak:          ac,
	}
}

func (s *Server) handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/akprox/ping" {
		w.WriteHeader(204)
		return
	}
	handler, ok := s.Handlers[r.Host]
	if !ok {
		// If we only have one handler, host name switching doesn't matter
		if len(s.Handlers) == 1 {
			for k := range s.Handlers {
				s.Handlers[k].ServeHTTP(w, r)
				return
			}
		}
		s.logger.WithField("host", r.Host).Debug("Host header does not match any we know of")
		s.logger.Printf("%v+\n", s.Handlers)
		w.WriteHeader(400)
		return
	}
	s.logger.WithField("host", r.Host).Debug("passing request from host head")
	handler.ServeHTTP(w, r)
}

func (s *Server) serve(listener net.Listener) {
	srv := &http.Server{Handler: http.HandlerFunc(s.handler)}

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
