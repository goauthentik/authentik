package ak

import (
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"

	"goauthentik.io/outpost/pkg/client/outposts"
	"goauthentik.io/outpost/pkg/models"
)

func (a *APIController) Update() ([]*models.ProxyOutpostConfig, error) {
	providers, err := a.Client.Outposts.OutpostsProxyList(outposts.NewOutpostsProxyListParams(), a.Auth)
	if err != nil {
		a.logger.WithError(err).Error("Failed to fetch providers")
		return nil, err
	}
	// Check provider hash to see if anything is changed
	hasher := sha512.New()
	out, err := json.Marshal(providers.Payload.Results)
	if err != nil {
		return nil, nil
	}
	hash := hex.EncodeToString(hasher.Sum(out))
	if hash == a.lastBundleHash {
		return nil, nil
	}
	a.lastBundleHash = hash
	return providers.Payload.Results, nil
}
