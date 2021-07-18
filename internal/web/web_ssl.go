package web

import (
	"crypto/tls"
	"net"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
)

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ws *WebServer) listenTLS() {
	cert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		ws.log.WithError(err).Error("failed to generate default cert")
	}
	tlsConfig := &tls.Config{
		MinVersion:   tls.VersionTLS12,
		MaxVersion:   tls.VersionTLS12,
		Certificates: []tls.Certificate{cert},
	}

	ln, err := net.Listen("tcp", config.G.Web.ListenTLS)
	if err != nil {
		ws.log.WithError(err).Fatalf("failed to listen")
		return
	}
	ws.log.WithField("addr", config.G.Web.ListenTLS).Info("Running")

	tlsListener := tls.NewListener(tcpKeepAliveListener{ln.(*net.TCPListener)}, tlsConfig)
	ws.serve(tlsListener)
	ws.log.Printf("closing %s", tlsListener.Addr())
}
