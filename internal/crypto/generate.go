package crypto

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"time"

	"go.uber.org/zap"
	"goauthentik.io/internal/config"
)

// GenerateSelfSignedCert Generate a self-signed TLS Certificate, to be used as fallback
func GenerateSelfSignedCert() (tls.Certificate, error) {
	l := config.Get().Logger()
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		l.Warn("Failed to generate private key", zap.Error(err))
		return tls.Certificate{}, err
	}

	keyUsage := x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment

	notBefore := time.Now()
	notAfter := notBefore.Add(365 * 24 * time.Hour)

	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, err := rand.Int(rand.Reader, serialNumberLimit)
	if err != nil {
		l.Warn("Failed to generate serial number", zap.Error(err))
		return tls.Certificate{}, err
	}

	template := x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			Organization: []string{"authentik"},
			CommonName:   "authentik default certificate",
		},
		NotBefore: notBefore,
		NotAfter:  notAfter,

		KeyUsage:              keyUsage,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		BasicConstraintsValid: true,
	}

	template.DNSNames = []string{"*"}

	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	if err != nil {
		l.Panic("failed to parse certificate", zap.Error(err))
	}
	pemBytes := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: derBytes})
	privBytes, err := x509.MarshalPKCS8PrivateKey(priv)
	if err != nil {
		l.Panic("failed to parse private key", zap.Error(err))
	}
	privPemByes := pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: privBytes})
	return tls.X509KeyPair(pemBytes, privPemByes)
}
