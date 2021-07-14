package ak

import (
	"context"
	"fmt"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"time"

	"github.com/go-openapi/strfmt"
	"github.com/google/uuid"
	"github.com/pkg/errors"
	"github.com/recws-org/recws"
	"goauthentik.io/outpost/api"
	"goauthentik.io/outpost/pkg"

	log "github.com/sirupsen/logrus"
)

const ConfigLogLevel = "log_level"
const ConfigErrorReportingEnabled = "error_reporting_enabled"
const ConfigErrorReportingEnvironment = "error_reporting_environment"

// APIController main controller which connects to the authentik api via http and ws
type APIController struct {
	Client *api.APIClient
	token  string

	Server Outpost

	logger *log.Entry

	reloadOffset time.Duration

	wsConn       *recws.RecConn
	instanceUUID uuid.UUID
}

// NewAPIController initialise new API Controller instance from URL and API token
func NewAPIController(akURL url.URL, token string) *APIController {
	config := api.NewConfiguration()
	config.UserAgent = pkg.UserAgent()
	config.Host = akURL.Host
	config.Scheme = akURL.Scheme
	config.HTTPClient = &http.Client{
		Transport: GetTLSTransport(),
	}
	config.AddDefaultHeader("Authorization", fmt.Sprintf("Bearer %s", token))

	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	log := log.WithField("logger", "authentik.outpost.ak-api-controller")

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, _, err := apiClient.OutpostsApi.OutpostsInstancesList(context.Background()).Execute()

	if err != nil {
		log.WithError(err).Error("Failed to fetch configuration")
		os.Exit(1)
	}
	outpost := outposts.Results[0]
	doGlobalSetup(outpost.Config)

	ac := &APIController{
		Client: apiClient,
		token:  token,

		logger: log,

		reloadOffset: time.Duration(rand.Intn(10)) * time.Second,
		instanceUUID: uuid.New(),
	}
	ac.logger.Debugf("HA Reload offset: %s", ac.reloadOffset)
	ac.initWS(akURL, strfmt.UUID(outpost.Pk))
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
