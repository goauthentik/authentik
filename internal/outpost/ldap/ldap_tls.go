package ldap

import (
	"crypto/tls"
	"net"

	"github.com/pires/go-proxyproto"
)

func (ls *LDAPServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	if len(ls.providers) == 1 {
		if ls.providers[0].cert != nil {
			ls.log.WithField("server-name", info.ServerName).Debug("We only have a single provider, using their cert")
			return ls.providers[0].cert, nil
		}
	}
	for _, provider := range ls.providers {
		if provider.tlsServerName == &info.ServerName {
			if provider.cert == nil {
				ls.log.WithField("server-name", info.ServerName).Debug("Handler does not have a certificate")
				return ls.defaultCert, nil
			}
			return provider.cert, nil
		}
	}
	ls.log.WithField("server-name", info.ServerName).Debug("Fallback to default cert")
	return ls.defaultCert, nil
}

func (ls *LDAPServer) StartLDAPTLSServer() error {
	listen := "0.0.0.0:6636"
	tlsConfig := &tls.Config{
		MinVersion:     tls.VersionTLS12,
		MaxVersion:     tls.VersionTLS12,
		GetCertificate: ls.getCertificates,
	}

	ln, err := net.Listen("tcp", listen)
	if err != nil {
		ls.log.WithField("listen", listen).WithError(err).Fatalf("FATAL: listen failed")
	}

	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	tln := tls.NewListener(proxyListener, tlsConfig)

	ls.log.WithField("listen", listen).Info("Starting ldap tls server")
	err = ls.s.Serve(tln)
	if err != nil {
		return err
	}
	ls.log.Printf("closing %s", ln.Addr())
	return ls.s.ListenAndServe(listen)
}
