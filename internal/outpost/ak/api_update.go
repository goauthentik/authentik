package ak

import (
	"context"

	"goauthentik.io/outpost/api"
)

func (a *APIController) Update() ([]api.ProxyOutpostConfig, error) {
	providers, _, err := a.Client.OutpostsApi.OutpostsProxyList(context.Background()).Execute()
	if err != nil {
		a.logger.WithError(err).Error("Failed to fetch providers")
		return nil, err
	}
	return providers.Results, nil
}
