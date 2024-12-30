package ak

import (
	"context"
	"crypto/tls"

	"go.uber.org/zap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
)

type CryptoStore struct {
	api *api.CryptoApiService

	log *zap.Logger

	fingerprints map[string]string
	certificates map[string]*tls.Certificate
}

func NewCryptoStore(cryptoApi *api.CryptoApiService) *CryptoStore {
	return &CryptoStore{
		api:          cryptoApi,
		log:          config.Get().Logger().Named("authentik.outpost.cryptostore"),
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
		cs.log.Warn("Failed to fetch certificate's fingerprint", zap.String("uuid", uuid), zap.Error(err))
		return ""
	}
	return kp.GetFingerprintSha256()
}

func (cs *CryptoStore) Fetch(uuid string) error {
	cfp := cs.getFingerprint(uuid)
	if cfp == cs.fingerprints[uuid] {
		cs.log.Debug("Fingerprint hasn't changed, not fetching cert", zap.String("uuid", uuid))
		return nil
	}
	cs.log.Info("Fetching certificate and private key", zap.String("uuid", uuid))

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
		cs.log.Warn("failed to fetch certificate", zap.Error(err))
	}
	return cs.certificates[uuid]
}
