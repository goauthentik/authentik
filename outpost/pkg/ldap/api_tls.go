package ldap

import "crypto/tls"

func (ls *LDAPServer) getCertificates(info *tls.ClientHelloInfo) (*tls.Certificate, error) {
	if len(ls.providers) == 1 {
		return ls.providers[0].cert, nil
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
	return ls.defaultCert, nil
}
