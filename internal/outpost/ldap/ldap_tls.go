package ldap

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils"
)

func (ls *LDAPServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	if len(ls.providers) == 1 {
		if ls.providers[0].cert != nil {
			ls.log.Debug("We only have a single provider, using their cert", zap.String("server-name", info.ServerName))
			return ls.providers[0].cert, nil
		}
	}
	allIdenticalCerts := true
	for _, provider := range ls.providers {
		if provider.tlsServerName == &info.ServerName {
			if provider.cert == nil {
				ls.log.Debug("Handler does not have a certificate", zap.String("server-name", info.ServerName))
				return ls.defaultCert, nil
			}
			return provider.cert, nil
		}
		if provider.certUUID != ls.providers[0].certUUID || provider.cert == nil {
			allIdenticalCerts = false
		}
	}
	if allIdenticalCerts {
		ls.log.Debug("all providers have the same keypair, using keypair", zap.String("server-name", info.ServerName))
		return ls.providers[0].cert, nil
	}
	ls.log.Debug("Fallback to default cert", zap.String("server-name", info.ServerName))
	return ls.defaultCert, nil
}

func (ls *LDAPServer) StartLDAPTLSServer() error {
	listen := config.Get().Listen.LDAPS
	tlsConfig := utils.GetTLSConfig()
	tlsConfig.GetCertificate = ls.getCertificates

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.Warn("Failed to listen", zap.String("listen", listen), zap.Error(err))
		return err
	}

	proxyListener := &proxyproto.Listener{Listener: ln, ConnPolicy: utils.GetProxyConnectionPolicy()}
	defer proxyListener.Close()

	tln := tls.NewListener(proxyListener, tlsConfig)

	ls.log.Info("Starting LDAP SSL server", zap.String("listen", listen))
	err = ls.s.Serve(tln)
	if err != nil {
		return err
	}
	ls.log.Info("Stopping LDAP SSL Server", zap.String("listen", listen))
	return nil
}
