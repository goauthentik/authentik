package proxyv2

import (
	"context"
	"fmt"
	"net/http"

	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
)

func (ps *ProxyServer) Refresh() error {
	providers, _, err := ps.akAPI.Client.OutpostsApi.OutpostsProxyList(context.Background()).Execute()
	if err != nil {
		ps.log.WithError(err).Error("Failed to fetch providers")
	}
	if err != nil {
		return err
	}
	apps := make(map[string]*application.Application)
	for _, provider := range providers.Results {
		ua := fmt.Sprintf(" (provider=%s)", provider.Name)
		hc := &http.Client{
			Transport: ak.NewUserAgentTransport(constants.OutpostUserAgent()+ua, ak.NewTracingTransport(context.TODO(), ak.GetTLSTransport())),
		}
		a, err := application.NewApplication(provider, hc, ps.cryptoStore, ps.akAPI)
		if err != nil {
			ps.log.WithError(err).Warning("failed to setup application")
		} else {
			apps[a.Host] = a
		}
	}
	ps.apps = apps
	ps.log.Debug("Swapped maps")
	return nil
}
