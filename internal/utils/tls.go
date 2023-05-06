package utils

import "crypto/tls"

func GetTLSConfig() *tls.Config {
	tlsConfig := &tls.Config{
		MinVersion: tls.VersionTLS12,
		MaxVersion: tls.VersionTLS12,
	}

	// Insecure SWEET32 attack ciphers, TLS config uses a fallback
	insecureCiphersIds := []uint16{
		tls.TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA,
		tls.TLS_RSA_WITH_3DES_EDE_CBC_SHA,
	}
	defaultSecureCiphers := []uint16{}
	for _, cs := range tls.CipherSuites() {
		for _, icsId := range insecureCiphersIds {
			if cs.ID != icsId {
				defaultSecureCiphers = append(defaultSecureCiphers, cs.ID)
			}
		}
	}
	tlsConfig.CipherSuites = defaultSecureCiphers
	return tlsConfig
}
