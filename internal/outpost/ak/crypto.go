package ak

import (
	"context"
	"crypto/tls"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

type CryptoStore struct {
	api *api.CryptoApiService

	log *log.Entry

	fingerprints map[string]string
	certificates map[string]*tls.Certificate
}

func NewCryptoStore(cryptoApi *api.CryptoApiService) *CryptoStore {
	return &CryptoStore{
		api:          cryptoApi,
		log:          log.WithField("logger", "authentik.outpost.cryptostore"),
		fingerprints: make(map[string]string),
		certificates: make(map[string]*tls.Certificate),
	}
}

func (cs *CryptoStore) AddKeypair(uuid string) error {
	// If they keypair was already added, don't
	// do it again
	if _, ok := cs.fingerprints[uuid]; ok {
		return nil
	}
	// reset fingerprint to force update
	cs.fingerprints[uuid] = ""
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
	if cfp == cs.fingerprints[uuid] {
		cs.log.WithField("uuid", uuid).Debug("Fingerprint hasn't changed, not fetching cert")
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

	x509cert, err := tls.X509KeyPair([]byte(cert.Data), []byte(key.Data))
	if err != nil {
		return err
	}
	cs.certificates[uuid] = &x509cert
	cs.fingerprints[uuid] = cfp
	return nil
}

func (cs *CryptoStore) Get(uuid string) *tls.Certificate {
	err := cs.Fetch(uuid)
	if err != nil {
		cs.log.WithError(err).Warning("failed to fetch certificate")
	}
	return cs.certificates[uuid]
}
