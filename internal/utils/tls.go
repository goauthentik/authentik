package utils

import (
	"crypto/tls"
	"slices"
)

func GetTLSConfig() *tls.Config {
	// Based on
	// https://ssl-config.mozilla.org/#server=go&version=1.25&config=intermediate&guideline=5.7
	tlsConfig := &tls.Config{
		MinVersion: tls.VersionTLS12,
		CurvePreferences: []tls.CurveID{
			tls.X25519,
			tls.CurveP256,
			tls.CurveP384,
		},
		PreferServerCipherSuites: true,
		CipherSuites:             []uint16{},
	}

	excludedCiphers := []uint16{
		// ChaCha20 is not FIPS validated
		tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
		tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
		// Insecure SWEET32 attack ciphers, TLS config uses a fallback
		tls.TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA,
		tls.TLS_RSA_WITH_3DES_EDE_CBC_SHA,
	}

	defaultSecureCiphers := []uint16{}
	for _, cs := range tls.CipherSuites() {
		if slices.Contains(excludedCiphers, cs.ID) {
			continue
		}
		defaultSecureCiphers = append(defaultSecureCiphers, cs.ID)
	}
	tlsConfig.CipherSuites = defaultSecureCiphers
	return tlsConfig
}
