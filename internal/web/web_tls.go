package web

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"
	"go.uber.org/zap"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/utils"
	"goauthentik.io/internal/utils/web"
)

func (ws *WebServer) GetCertificate() func(ch *tls.ClientHelloInfo) (*tls.Certificate, error) {
	cert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		ws.log.Error("failed to generate default cert", zap.Error(err))
	}
	return func(ch *tls.ClientHelloInfo) (*tls.Certificate, error) {
		if ch.ServerName == "" {
			return &cert, nil
		}
		if ws.ProxyServer != nil {
			appCert := ws.ProxyServer.GetCertificate(ch.ServerName)
			if appCert != nil {
				return appCert, nil
			}
		}
		if ws.BrandTLS != nil {
			return ws.BrandTLS.GetCertificate(ch)
		}
		ws.log.Debug("using default, self-signed certificate", config.Trace())
		return &cert, nil
	}
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ws *WebServer) listenTLS() {
	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetCertificate = ws.GetCertificate()

	ln, err := net.Listen("tcp", config.Get().Listen.HTTPS)
	if err != nil {
		ws.log.Warn("failed to listen (TLS)", zap.Error(err))
		return
	}
	proxyListener := &proxyproto.Listener{
		Listener: web.TCPKeepAliveListener{
			TCPListener: ln.(*net.TCPListener),
			Logger:      ws.log,
		},
		ConnPolicy: utils.GetProxyConnectionPolicy(),
	}
	defer proxyListener.Close()

	tlsListener := tls.NewListener(proxyListener, tlsConfig)
	ws.log.Info("Starting HTTPS server", zap.String("listen", config.Get().Listen.HTTPS))
	ws.serve(tlsListener)
	ws.log.Info("Stopping HTTPS server", zap.String("listen", config.Get().Listen.HTTPS))
}
