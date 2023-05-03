package ldap

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"
	"goauthentik.io/internal/config"
)

func (ls *LDAPServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	if len(ls.providers) == 1 {
		if ls.providers[0].cert != nil {
			ls.log.WithField("server-name", info.ServerName).Debug("We only have a single provider, using their cert")
			return ls.providers[0].cert, nil
		}
	}
	allIdenticalCerts := true
	for _, provider := range ls.providers {
		if provider.tlsServerName == &info.ServerName {
			if provider.cert == nil {
				ls.log.WithField("server-name", info.ServerName).Debug("Handler does not have a certificate")
				return ls.defaultCert, nil
			}
			return provider.cert, nil
		}
		if provider.certUUID != ls.providers[0].certUUID || provider.cert == nil {
			allIdenticalCerts = false
		}
	}
	if allIdenticalCerts {
		ls.log.WithField("server-name", info.ServerName).Debug("all providers have the same keypair, using keypair")
		return ls.providers[0].cert, nil
	}
	ls.log.WithField("server-name", info.ServerName).Debug("Fallback to default cert")
	return ls.defaultCert, nil
}

func (ls *LDAPServer) StartLDAPTLSServer() error {
	listen := config.Get().Listen.LDAPS
	tlsConfig := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ls.getCertificates,
	}

	// Insecure SWEET32 attack ciphers, TLS config uses a fallback
	insecureCiphersIds := []uint16{
		tls.TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA,
		tls.TLS_RSA_WITH_3DES_EDE_CBC_SHA,
	}
	defaultSecureCiphers := []uint16{}
	for _, cs := range tls.CipherSuites() {
		csID := cs.ID
		for _, icsId := range insecureCiphersIds {
			if csID != icsId {
				defaultSecureCiphers = append(defaultSecureCiphers, csID)
			}
		}
	}
	tlsConfig.CipherSuites = defaultSecureCiphers

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.WithField("listen", listen).WithError(err).Warning("Failed to listen")
		return err
	}

	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	tln := tls.NewListener(proxyListener, tlsConfig)

	ls.log.WithField("listen", listen).Info("Starting LDAP SSL server")
	err = ls.s.Serve(tln)
	if err != nil {
		return err
	}
	ls.log.WithField("listen", listen).Info("Stopping LDAP SSL Server")
	return nil
}
