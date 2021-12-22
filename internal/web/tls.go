package web

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
)

func (ws *WebServer) GetCertificate() func(ch *tls.ClientHelloInfo) (*tls.Certificate, error) {
	cert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		ws.log.WithError(err).Error("failed to generate default cert")
	}
	return func(ch *tls.ClientHelloInfo) (*tls.Certificate, error) {
		if ws.ProxyServer != nil {
			appCert := ws.ProxyServer.GetCertificate(ch.ServerName)
			if appCert != nil {
				return appCert, nil
			}
		}
		ws.log.Trace("using default, self-signed certificate")
		return &cert, nil
	}
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ws *WebServer) listenTLS() {
	tlsConfig := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ws.GetCertificate(),
	}

	ln, err := net.Listen("tcp", config.G.Web.ListenTLS)
	if err != nil {
		ws.log.WithError(err).Fatalf("failed to listen")
		return
	}
	ws.log.WithField("listen", config.G.Web.ListenTLS).Info("Listening (TLS)")

	proxyListener := &proxyproto.Listener{Listener: tcpKeepAliveListener{ln.(*net.TCPListener)}}
	defer proxyListener.Close()

	tlsListener := tls.NewListener(proxyListener, tlsConfig)
	ws.serve(tlsListener)
	ws.log.Printf("closing %s", tlsListener.Addr())
}
