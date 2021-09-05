package proxy

import (
	"net/url"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
)

func (s *Server) Refresh() error {
	providers, err := s.ak.Update()
	if err != nil {
		return err
	}
	if providers == nil {
		s.logger.Debug("Providers have not changed, not updating")
		return nil
	}
	bundles := s.bundleProviders(providers)
	s.updateHTTPServer(bundles)
	return nil
}

func (s *Server) bundleProviders(providers []api.ProxyOutpostConfig) []*providerBundle {
	bundles := make([]*providerBundle, len(providers))
	for idx, provider := range providers {
		externalHost, err := url.Parse(provider.ExternalHost)
		if err != nil {
			log.WithError(err).Warning("Failed to parse URL, skipping provider")
		}
		bundles[idx] = &providerBundle{
			s:             s,
			Host:          externalHost.Host,
			log:           log.WithField("logger", "authentik.outpost.proxy-bundle").WithField("provider", provider.Name),
			endSessionUrl: provider.OidcConfiguration.EndSessionEndpoint,
		}
		bundles[idx].Build(provider)
	}
	return bundles
}

func (s *Server) updateHTTPServer(bundles []*providerBundle) {
	newMap := make(map[string]*providerBundle)
	for _, bundle := range bundles {
		newMap[bundle.Host] = bundle
	}
	s.logger.Debug("Swapped maps")
	s.Handlers = newMap
}
