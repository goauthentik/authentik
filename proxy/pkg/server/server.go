package server

import (
	"context"
	"crypto/tls"
	"errors"
	"net"
	"net/http"
	"time"

	log "github.com/sirupsen/logrus"

	sentryhttp "github.com/getsentry/sentry-go/http"
)

// Server represents an HTTP server
type Server struct {
	Handlers map[string]*providerBundle

	stop   chan struct{} // channel for waiting shutdown
	logger *log.Entry

	defaultCert tls.Certificate
}

// NewServer initialise a new HTTP Server
func NewServer() *Server {
	defaultCert, err := generateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	return &Server{
		Handlers:    make(map[string]*providerBundle),
		logger:      log.WithField("component", "http-server"),
		defaultCert: defaultCert,
	}
}

// ServeHTTP constructs a net.Listener and starts handling HTTP requests
func (s *Server) ServeHTTP() {
	// TODO: make this a setting
	listenAddress := "localhost:4180"
	listener, err := net.Listen("tcp", listenAddress)
	if err != nil {
		s.logger.Fatalf("FATAL: listen (%s) failed - %s", listenAddress, err)
	}
	s.logger.Printf("listening on %s", listener.Addr())
	s.serve(listener)
	s.logger.Printf("closing %s", listener.Addr())
}

func (s *Server) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	handler, ok := s.Handlers[info.ServerName]
	if !ok {
		s.logger.WithField("server-name", info.ServerName).Debug("Handler does not exist")
		return &s.defaultCert, nil
	}
	if handler.cert == nil {
		s.logger.WithField("server-name", info.ServerName).Debug("Handler does not have a certificate")
		return &s.defaultCert, nil
	}
	return handler.cert, nil
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (s *Server) ServeHTTPS() {
	// TODO: make this a setting
	listenAddress := "localhost:4443"
	config := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: s.getCertificates,
	}

	ln, err := net.Listen("tcp", listenAddress)
	if err != nil {
		s.logger.Fatalf("FATAL: listen (%s) failed - %s", listenAddress, err)
	}
	s.logger.Printf("listening on %s", ln.Addr())

	tlsListener := tls.NewListener(tcpKeepAliveListener{ln.(*net.TCPListener)}, config)
	s.serve(tlsListener)
	s.logger.Printf("closing %s", tlsListener.Addr())
}

func (s *Server) handler(w http.ResponseWriter, r *http.Request) {
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
	sentryHandler := sentryhttp.New(sentryhttp.Options{})

	srv := &http.Server{Handler: sentryHandler.HandleFunc(s.handler)}

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
