package ak

import (
	"fmt"
	"math/rand"
	"net/url"
	"time"

	"github.com/go-openapi/runtime"
	"github.com/pkg/errors"
	"github.com/recws-org/recws"
	"goauthentik.io/outpost/pkg"
	"goauthentik.io/outpost/pkg/client"
	"goauthentik.io/outpost/pkg/client/outposts"

	httptransport "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/strfmt"
	log "github.com/sirupsen/logrus"
)

const ConfigLogLevel = "log_level"
const ConfigErrorReportingEnabled = "error_reporting_enabled"
const ConfigErrorReportingEnvironment = "error_reporting_environment"

// APIController main controller which connects to the authentik api via http and ws
type APIController struct {
	Client *client.Authentik
	Auth   runtime.ClientAuthInfoWriter
	token  string

	Server Outpost

	lastBundleHash string
	logger         *log.Entry

	reloadOffset time.Duration

	wsConn *recws.RecConn
}

// NewAPIController initialise new API Controller instance from URL and API token
func NewAPIController(pbURL url.URL, token string) *APIController {
	transport := httptransport.New(pbURL.Host, client.DefaultBasePath, []string{pbURL.Scheme})
	transport.Transport = SetUserAgent(getTLSTransport(), fmt.Sprintf("authentik-proxy@%s", pkg.VERSION))

	// create the transport
	auth := httptransport.BasicAuth("", token)

	// create the API client, with the transport
	apiClient := client.New(transport, strfmt.Default)

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, err := apiClient.Outposts.OutpostsOutpostsList(outposts.NewOutpostsOutpostsListParams(), auth)

	if err != nil {
		panic(err)
	}
	outpost := outposts.Payload.Results[0]
	doGlobalSetup(outpost.Config.(map[string]interface{}))

	ac := &APIController{
		Client: apiClient,
		Auth:   auth,
		token:  token,

		logger: log.WithField("component", "ak-api-controller"),

		reloadOffset: time.Duration(rand.Intn(10)) * time.Second,

		lastBundleHash: "",
	}
	ac.logger.Debugf("HA Reload offset: %s", ac.reloadOffset)
	ac.initWS(pbURL, outpost.Pk)
	return ac
}

func (a *APIController) GetLastBundleHash() string {
	return a.lastBundleHash
}

// Start Starts all handlers, non-blocking
func (a *APIController) Start() error {
	err := a.Server.Refresh()
	if err != nil {
		return errors.Wrap(err, "failed to run initial refresh")
	}
	go func() {
		a.logger.Debug("Starting WS Handler...")
		a.startWSHandler()
	}()
	go func() {
		a.logger.Debug("Starting WS Health notifier...")
		a.startWSHealth()
	}()
	go func() {
		a.Server.Start()
	}()
	return nil
}
