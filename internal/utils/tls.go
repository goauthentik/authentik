package utils

import (
	"crypto/tls"
	"slices"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

func GetTLSConfig() *tls.Config {
	minVersion := uint16(tls.VersionTLS12)
	switch strings.ToUpper(config.Get().Outposts.TLSMinVersion) {
	case "TLS1.0", "TLSV1", "TLSV1.0", "TLSV1_0", "1.0":
		minVersion = tls.VersionTLS10
	case "TLS1.1", "TLSV1.1", "TLSV1_1", "1.1":
		minVersion = tls.VersionTLS11
	case "TLS1.2", "TLSV1.2", "TLSV1_2", "1.2":
		minVersion = tls.VersionTLS12
	case "TLS1.3", "TLSV1.3", "TLSV1_3", "1.3":
		minVersion = tls.VersionTLS13
	}

	// Based on
	// https://ssl-config.mozilla.org/#server=go&version=1.25&config=intermediate&guideline=5.7
	tlsConfig := &tls.Config{
		MinVersion: minVersion,
		CurvePreferences: []tls.CurveID{
			tls.X25519,
			tls.CurveP256,
			tls.CurveP384,
		},
		PreferServerCipherSuites: true,
		CipherSuites:             []uint16{},
	}

	configuredCiphers := config.Get().Outposts.TLSCiphers
	if len(configuredCiphers) > 0 {
		allCiphers := append(tls.CipherSuites(), tls.InsecureCipherSuites()...)
		for _, cipherName := range configuredCiphers {
			found := false
			for _, cs := range allCiphers {
				if cs.Name == cipherName {
					tlsConfig.CipherSuites = append(tlsConfig.CipherSuites, cs.ID)
					found = true
					break
				}
			}
			if !found {
				log.WithField("cipher", cipherName).Warning("Unknown TLS cipher suite configured")
			}
		}
		if len(tlsConfig.CipherSuites) > 0 {
			return tlsConfig
		}
		log.Warning("No valid TLS ciphers parsed from configuration, falling back to defaults")
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
