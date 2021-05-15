package ak

import (
	"math/rand"
	"net/url"
	"os"
	"time"

	"github.com/go-openapi/runtime"
	"github.com/google/uuid"
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

	logger *log.Entry

	reloadOffset time.Duration

	wsConn       *recws.RecConn
	instanceUUID uuid.UUID
}

// NewAPIController initialise new API Controller instance from URL and API token
func NewAPIController(akURL url.URL, token string) *APIController {
	transport := httptransport.New(akURL.Host, client.DefaultBasePath, []string{akURL.Scheme})
	transport.Transport = SetUserAgent(GetTLSTransport(), pkg.UserAgent())

	// create the transport
	auth := httptransport.BearerToken(token)

	// create the API client, with the transport
	apiClient := client.New(transport, strfmt.Default)

	log := log.WithField("logger", "authentik.outpost.ak-api-controller")

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, err := apiClient.Outposts.OutpostsInstancesList(outposts.NewOutpostsInstancesListParams(), auth)

	if err != nil {
		log.WithError(err).Error("Failed to fetch configuration")
		os.Exit(1)
	}
	outpost := outposts.Payload.Results[0]
	doGlobalSetup(outpost.Config.(map[string]interface{}))

	ac := &APIController{
		Client: apiClient,
		Auth:   auth,
		token:  token,

		logger: log,

		reloadOffset: time.Duration(rand.Intn(10)) * time.Second,
		instanceUUID: uuid.New(),
	}
	ac.logger.Debugf("HA Reload offset: %s", ac.reloadOffset)
	ac.initWS(akURL, outpost.Pk)
	return ac
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
		a.logger.Debug("Starting Interval updater...")
		a.startIntervalUpdater()
	}()
	go func() {
		err := a.Server.Start()
		if err != nil {
			panic(err)
		}
	}()
	return nil
}
