package web

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/utils"
	"goauthentik.io/internal/utils/web"
)

func (ws *WebServer) GetCertificate() func(ch *tls.ClientHelloInfo) (*tls.Config, error) {
	fallback, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		ws.log.WithError(err).Error("failed to generate default cert")
	}
	return func(ch *tls.ClientHelloInfo) (*tls.Config, error) {
		cfg := utils.GetTLSConfig()
		if ch.ServerName == "" {
			cfg.Certificates = []tls.Certificate{fallback}
			return cfg, nil
		}
		if ws.ProxyServer != nil {
			appCert := ws.ProxyServer.GetCertificate(ch.ServerName)
			if appCert != nil {
				cfg.Certificates = []tls.Certificate{*appCert}
				return cfg, nil
			}
		}
		if ws.BrandTLS != nil {
			bcert := ws.BrandTLS.GetCertificate(ch)
			cfg.Certificates = []tls.Certificate{*bcert.Web}
			ws.log.Trace("using brand web Certificate")
			if bcert.Client != nil {
				cfg.ClientCAs = bcert.Client
				cfg.ClientAuth = tls.RequestClientCert
				ws.log.Trace("using brand client Certificate")
			}
			return cfg, nil
		}
		ws.log.Trace("using default, self-signed certificate")
		cfg.Certificates = []tls.Certificate{fallback}
		return cfg, nil
	}
}

// ServeHTTPS constructs a net.Listener and starts handling HTTPS requests
func (ws *WebServer) listenTLS() {
	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetConfigForClient = ws.GetCertificate()

	ln, err := net.Listen("tcp", config.Get().Listen.HTTPS)
	if err != nil {
		ws.log.WithError(err).Warning("failed to listen (TLS)")
		return
	}
	proxyListener := &proxyproto.Listener{
		Listener: web.TCPKeepAliveListener{
			TCPListener: ln.(*net.TCPListener),
		},
		ConnPolicy: utils.GetProxyConnectionPolicy(),
	}
	defer func() {
		err := proxyListener.Close()
		if err != nil {
			ws.log.WithError(err).Warning("failed to close proxy listener")
		}
	}()

	tlsListener := tls.NewListener(proxyListener, tlsConfig)
	ws.log.WithField("listen", config.Get().Listen.HTTPS).Info("Starting HTTPS server")
	ws.serve(tlsListener)
	ws.log.WithField("listen", config.Get().Listen.HTTPS).Info("Stopping HTTPS server")
}
