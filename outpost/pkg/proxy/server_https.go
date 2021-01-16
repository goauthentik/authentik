package proxy

import (
	"crypto/tls"
	"net"
	"sync"
)

// ServeHTTP constructs a net.Listener and starts handling HTTP requests
func (s *Server) ServeHTTP() {
	listenAddress := "0.0.0.0:4180"
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
	listenAddress := "0.0.0.0:4443"
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

func (s *Server) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		s.logger.Debug("Starting HTTP Server...")
		s.ServeHTTP()
	}()
	go func() {
		defer wg.Done()
		s.logger.Debug("Starting HTTPs Server...")
		s.ServeHTTPS()
	}()
	return nil
}
