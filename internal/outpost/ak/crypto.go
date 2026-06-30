package ak

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"

	api "goauthentik.io/packages/client-go"
)

type CertCacheEntry struct {
	certificate *tls.Certificate
	fingerprint string
	refreshAt   time.Time
}

type CryptoStore struct {
	api *api.CryptoAPIService

	log *log.Entry

	certificates map[string]CertCacheEntry

	cacheTTL time.Duration
}

func NewCryptoStore(cryptoApi *api.CryptoAPIService) *CryptoStore {
	certificateCacheTTL := config.Get().AuthentikCertificateCacheTTL

	if certificateCacheTTL == 0 {
		certificateCacheTTL = 24 * time.Hour
	}

	return &CryptoStore{
		api:          cryptoApi,
		log:          log.WithField("logger", "authentik.outpost.cryptostore"),
		certificates: make(map[string]CertCacheEntry),
		cacheTTL:     certificateCacheTTL,
	}
}

func (cs *CryptoStore) AddKeypair(uuid string) error {
	// Check if the cached fingerprint matches the certificate,
	// if not, we re-fetch it
	if sfp, ok := cs.certificates[uuid]; ok {
		fp := cs.getFingerprint(uuid)
		if sfp.fingerprint == fp {
			return nil
		}
	}
	// reset fingerprint to force update
	if cert, ok := cs.certificates[uuid]; ok {
		cert.fingerprint = ""
	}

	err := cs.Fetch(uuid)
	if err != nil {
		return err
	}
	return nil
}

func (cs *CryptoStore) getFingerprint(uuid string) string {
	kp, _, err := cs.api.CryptoCertificatekeypairsRetrieve(context.Background(), uuid).Execute()
	if err != nil {
		cs.log.WithField("uuid", uuid).WithError(err).Warning("Failed to fetch certificate's fingerprint")
		return ""
	}
	return kp.GetFingerprintSha256()
}

func (cs *CryptoStore) Fetch(uuid string) error {
	cfp := cs.getFingerprint(uuid)
	if cert, ok := cs.certificates[uuid]; ok && cfp == cert.fingerprint {
		cs.log.WithField("uuid", uuid).Debug("Fingerprint hasn't changed, not fetching cert")
		cert.refreshAt = time.Now().Add(cs.cacheTTL)
		return nil
	}
	cs.log.WithField("uuid", uuid).Info("Fetching certificate and private key")

	cert, _, err := cs.api.CryptoCertificatekeypairsViewCertificateRetrieve(context.Background(), uuid).Execute()
	if err != nil {
		return err
	}
	key, _, err := cs.api.CryptoCertificatekeypairsViewPrivateKeyRetrieve(context.Background(), uuid).Execute()
	if err != nil {
		return err
	}

	var tcert tls.Certificate
	if key.Data != "" {
		x509cert, err := tls.X509KeyPair([]byte(cert.Data), []byte(key.Data))
		if err != nil {
			return err
		}
		tcert = x509cert
	} else {
		p, _ := pem.Decode([]byte(cert.Data))
		x509cert, err := x509.ParseCertificate(p.Bytes)
		if err != nil {
			return err
		}
		tcert = tls.Certificate{
			Certificate: [][]byte{x509cert.Raw},
			Leaf:        x509cert,
		}
	}

	cs.certificates[uuid] = CertCacheEntry{
		certificate: &tcert,
		fingerprint: cfp,
		refreshAt:   time.Now().Add(cs.cacheTTL),
	}

	return nil
}

func (cs *CryptoStore) Get(uuid string) *tls.Certificate {
	c, ok := cs.certificates[uuid]
	if ok && c.refreshAt.After(time.Now()) {
		return c.certificate
	}
	err := cs.Fetch(uuid)
	if err != nil {
		cs.log.WithError(err).Warning("failed to fetch certificate")
	}
	return cs.certificates[uuid].certificate
}
