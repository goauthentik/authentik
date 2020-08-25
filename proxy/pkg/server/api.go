package server

import (
	"crypto/sha512"
	"encoding/hex"
	"net/url"

	"github.com/BeryJu/passbook/proxy/pkg/client"
	"github.com/BeryJu/passbook/proxy/pkg/client/outposts"
	"github.com/go-openapi/runtime"
	"github.com/recws-org/recws"

	httptransport "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/strfmt"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	log "github.com/sirupsen/logrus"
)

type APIController struct {
	client *client.Passbook
	auth   runtime.ClientAuthInfoWriter
	token  string

	server *Server

	commonOpts *options.Options

	lastBundleHash string
	logger         *log.Entry

	wsConn recws.RecConn
}

func NewAPIController(pbURL url.URL, token string) *APIController {
	// create the transport
	transport := httptransport.New(pbURL.Host, client.DefaultBasePath, []string{pbURL.Scheme})
	auth := httptransport.BasicAuth("", token)

	// create the API client, with the transport
	apiClient := client.New(transport, strfmt.Default)

	commonOpts := options.NewOptions()
	commonOpts.Cookie.Name = "passbook_proxy"
	commonOpts.EmailDomains = []string{"*"}
	commonOpts.ProviderType = "oidc"
	commonOpts.ProxyPrefix = "/pbprox"
	commonOpts.SkipProviderButton = true
	commonOpts.Logging.SilencePing = true

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, err := apiClient.Outposts.OutpostsOutpostsList(outposts.NewOutpostsOutpostsListParams(), auth)

	if err != nil {
		panic(err)
	}
	outpost := outposts.Payload.Results[0]

	ac := &APIController{
		client:         apiClient,
		auth:           auth,
		token:          token,
		logger:         log.WithField("component", "api-controller"),
		commonOpts:     commonOpts,
		server:         NewServer(),
		lastBundleHash: "",
	}
	ac.initWS(pbURL, outpost.Pk)
	return ac
}

func (a *APIController) bundleProviders() ([]*ProviderBundle, error) {
	providers, err := a.client.Outposts.OutpostsProxyList(outposts.NewOutpostsProxyListParams(), a.auth)
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
	go func() {
		a.logger.Debug("Starting HTTP Server...")
		a.server.ServeHTTP()
	}()
	go func() {
		a.logger.Debug("Starting HTTPs Server...")
		a.server.ServeHTTPS()
	}()
	go func() {
		a.logger.Debug("Starting WS Handler...")
		a.startWSHandler()
	}()
	go func() {
		a.logger.Debug("Starting WS Health notifier...")
		a.startWSHealth()
	}()
	return nil
}
