package ak

import (
	"goauthentik.io/outpost/pkg/client/outposts"
	"goauthentik.io/outpost/pkg/models"
)

func (a *APIController) Update() ([]*models.ProxyOutpostConfig, error) {
	providers, err := a.Client.Outposts.OutpostsProxyList(outposts.NewOutpostsProxyListParams(), a.Auth)
	if err != nil {
		a.logger.WithError(err).Error("Failed to fetch providers")
		return nil, err
	}
	return providers.Payload.Results, nil
}
