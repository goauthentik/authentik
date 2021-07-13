package ldap

import "crypto/tls"

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
