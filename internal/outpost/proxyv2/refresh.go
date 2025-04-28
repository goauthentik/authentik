package proxyv2

import (
	"context"
	"fmt"
	"net/http"
	"net/url"

	"github.com/getsentry/sentry-go"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
	"goauthentik.io/internal/utils/web"
	"golang.org/x/exp/maps"
)

func (ps *ProxyServer) Refresh() error {
	providers, err := ak.Paginator(ps.akAPI.Client.OutpostsApi.OutpostsProxyList(context.Background()), ak.PaginatorOptions{
		PageSize: 100,
		Logger:   ps.log,
	})
	if err != nil {
		ps.log.WithError(err).Error("Failed to fetch providers")
	}
	if err != nil {
		return err
	}
	apps := make(map[string]*application.Application)
	for _, provider := range providers {
		rsp := sentry.StartSpan(context.Background(), "authentik.outposts.proxy.application_ss")
		ua := fmt.Sprintf(" (provider=%s)", provider.Name)
		hc := &http.Client{
			Transport: web.NewUserAgentTransport(
				constants.UserAgentOutpost()+ua,
				web.NewTracingTransport(
					rsp.Context(),
					ak.GetTLSTransport(),
				),
			),
		}
		externalHost, err := url.Parse(provider.ExternalHost)
		if err != nil {
			ps.log.WithError(err).Warning("failed to parse URL, skipping provider")
			continue
		}
		existing, ok := ps.apps[externalHost.Host]
		a, err := application.NewApplication(provider, hc, ps, existing)
		if ok {
			existing.Stop()
		}
		if err != nil {
			ps.log.WithError(err).Warning("failed to setup application")
			continue
		}
		apps[externalHost.Host] = a
	}
	ps.apps = apps
	ps.log.Debug("Swapped maps")
	return nil
}

func (ps *ProxyServer) API() *ak.APIController {
	return ps.akAPI
}

func (ps *ProxyServer) CryptoStore() *ak.CryptoStore {
	return ps.cryptoStore
}

func (ps *ProxyServer) Apps() []*application.Application {
	return maps.Values(ps.apps)
}
