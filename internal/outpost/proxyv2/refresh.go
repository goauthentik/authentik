package proxyv2

import (
	"context"
	"fmt"
	"net/http"

	"github.com/getsentry/sentry-go"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
	"goauthentik.io/internal/utils/web"
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
		rsp := sentry.StartSpan(context.Background(), "authentik.outposts.proxy.application_ss")
		ua := fmt.Sprintf(" (provider=%s)", provider.Name)
		hc := &http.Client{
			Transport: web.NewUserAgentTransport(
				constants.OutpostUserAgent()+ua,
				web.NewTracingTransport(
					rsp.Context(),
					ak.GetTLSTransport(),
				),
			),
		}
		a, err := application.NewApplication(provider, hc, ps.cryptoStore, ps.akAPI)
		existing, ok := apps[a.Host]
		if ok {
			existing.Stop()
		}
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
