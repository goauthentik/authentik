package ak

import (
	"crypto/sha512"
	"encoding/hex"

	"github.com/BeryJu/authentik/outpost/pkg/client/outposts"
	"github.com/BeryJu/authentik/outpost/pkg/models"
)

func (a *APIController) Update() ([]*models.ProxyOutpostConfig, error) {
	providers, err := a.Client.Outposts.OutpostsProxyList(outposts.NewOutpostsProxyListParams(), a.Auth)
	if err != nil {
		a.logger.WithError(err).Error("Failed to fetch providers")
		return nil, err
	}
	// Check provider hash to see if anything is changed
	hasher := sha512.New()
	bin, _ := providers.Payload.MarshalBinary()
	hash := hex.EncodeToString(hasher.Sum(bin))
	if hash == a.lastBundleHash {
		return nil, nil
	}
	a.lastBundleHash = hash
	return providers.Payload.Results, nil
}
