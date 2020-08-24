package server

import (
	"context"
	"crypto/sha512"
	"encoding/hex"
	"net/url"
	"sync"
	"time"

	"github.com/BeryJu/passbook/proxy/pkg/client"
	"github.com/BeryJu/passbook/proxy/pkg/client/providers"
	"github.com/go-openapi/runtime"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	log "github.com/sirupsen/logrus"
)

type APIController struct {
	client *client.Passbook
	auth   runtime.ClientAuthInfoWriter

	server *Server

	commonOpts *options.Options

	lastBundleHash string
	logger         *log.Entry
}

func NewAPIController(client *client.Passbook, auth runtime.ClientAuthInfoWriter) *APIController {
	commonOpts := options.NewOptions()
	commonOpts.Cookie.Name = "passbook_proxy"
	commonOpts.EmailDomains = []string{"*"}
	commonOpts.ProviderType = "oidc"
	commonOpts.ProxyPrefix = "/pbprox"
	commonOpts.SkipProviderButton = true
	commonOpts.Logging.SilencePing = true

	return &APIController{
		client:         client,
		auth:           auth,
		logger:         log.WithField("component", "api-controller"),
		commonOpts:     commonOpts,
		server:         NewServer(),
		lastBundleHash: "",
	}
}

func (a *APIController) bundleProviders() ([]*ProviderBundle, error) {
	providers, err := a.client.Providers.ProvidersProxyList(&providers.ProvidersProxyListParams{
		Context: context.Background(),
	}, a.auth)
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

	bundles := make([]*ProviderBundle, len(providers.Payload.Results))

	for idx, provider := range providers.Payload.Results {
		externalHost, err := url.Parse(*provider.ExternalHost)
		if err != nil {
			log.WithError(err).Warning("Failed to parse URL, skipping provider")
		}
		bundles[idx] = &ProviderBundle{
			a:    a,
			Host: externalHost.Hostname(),
		}
		bundles[idx].Build(provider)
	}
	return bundles, nil
}

func (a *APIController) updateHTTPServer(bundles []*ProviderBundle) {
	newMap := make(map[string]*ProviderBundle)
	for _, bundle := range bundles {
		newMap[bundle.Host] = bundle
	}
	a.logger.Debug("Swapped maps")
	a.server.Handlers = newMap
}

func (a *APIController) UpdateIfRequired() error {
	bundles, err := a.bundleProviders()
	if err != nil {
		return err
	}
	if bundles == nil {
		a.logger.Debug("Providers have not changed, not updating")
		return nil
	}
	a.updateHTTPServer(bundles)
	return nil
}

func (a *APIController) Start() error {
	err := a.UpdateIfRequired()
	if err != nil {
		return err
	}
	wg := sync.WaitGroup{}
	wg.Add(3)
	go func() {
		a.logger.Debug("Starting HTTP Server...")
		a.server.ServeHTTP()
		defer wg.Done()
	}()
	go func() {
		a.logger.Debug("Starting HTTPs Server...")
		a.server.ServeHTTPS()
		defer wg.Done()
	}()
	ticker := time.NewTicker(30 * time.Second)
	quit := make(chan struct{})
	go func() {
		a.logger.Debug("Starting API Update time...")
		defer wg.Done()
		for {
			select {
			case <-ticker.C:
				a.logger.Debug("Updating providers from passbook")
				err := a.UpdateIfRequired()
				if err != nil {
					a.logger.WithError(err).Warning("Failed to update providers")
				}
			case <-quit:
				ticker.Stop()
				return
			}
		}
	}()
	wg.Wait()
	return nil
}
