package ak

import (
	"context"
	"fmt"
	"math/rand"
	"net/http"
	"net/url"
	"time"

	"github.com/go-openapi/strfmt"
	"github.com/google/uuid"
	"github.com/pkg/errors"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/recws-org/recws"
	"goauthentik.io/api"
	"goauthentik.io/internal/constants"

	log "github.com/sirupsen/logrus"
)

const ConfigLogLevel = "log_level"
const ConfigErrorReportingEnabled = "error_reporting_enabled"
const ConfigErrorReportingEnvironment = "error_reporting_environment"

// APIController main controller which connects to the authentik api via http and ws
type APIController struct {
	Client       *api.APIClient
	Outpost      api.Outpost
	GlobalConfig api.Config

	Server Outpost

	token string

	logger *log.Entry

	reloadOffset time.Duration

	wsConn       *recws.RecConn
	instanceUUID uuid.UUID
}

// NewAPIController initialise new API Controller instance from URL and API token
func NewAPIController(akURL url.URL, token string) *APIController {
	config := api.NewConfiguration()
	config.Host = akURL.Host
	config.Scheme = akURL.Scheme
	config.HTTPClient = &http.Client{
		Transport: NewUserAgentTransport(constants.OutpostUserAgent(), NewTracingTransport(context.TODO(), GetTLSTransport())),
	}
	config.AddDefaultHeader("Authorization", fmt.Sprintf("Bearer %s", token))

	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	log := log.WithField("logger", "authentik.outpost.ak-api-controller")

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, _, err := apiClient.OutpostsApi.OutpostsInstancesList(context.Background()).Execute()

	if err != nil {
		log.WithError(err).Error("Failed to fetch outpost configuration")
		return nil
	}
	outpost := outposts.Results[0]
	doGlobalSetup(outpost.Config)

	log.WithField("name", outpost.Name).Debug("Fetched outpost configuration")

	akConfig, _, err := apiClient.RootApi.RootConfigRetrieve(context.Background()).Execute()
	if err != nil {
		log.WithError(err).Error("Failed to fetch global configuration")
		return nil
	}
	log.Debug("Fetched global configuration")

	ac := &APIController{
		Client:       apiClient,
		GlobalConfig: akConfig,

		token:  token,
		logger: log,

		reloadOffset: time.Duration(rand.Intn(10)) * time.Second,
		instanceUUID: uuid.New(),
		Outpost:      outpost,
	}
	ac.logger.Debugf("HA Reload offset: %s", ac.reloadOffset)
	ac.initWS(akURL, strfmt.UUID(outpost.Pk))

	OutpostInfo.With(prometheus.Labels{
		"uuid":    ac.instanceUUID.String(),
		"name":    outpost.Name,
		"version": constants.VERSION,
		"build":   constants.BUILD(),
	}).Set(1)
	return ac
}

// Start Starts all handlers, non-blocking
func (a *APIController) Start() error {
	err := a.StartBackgorundTasks()
	if err != nil {
		return err
	}
	go func() {
		err := a.Server.Start()
		if err != nil {
			panic(err)
		}
	}()
	return nil
}

func (a *APIController) StartBackgorundTasks() error {
	err := a.Server.Refresh()
	if err != nil {
		return errors.Wrap(err, "failed to run initial refresh")
	} else {
		LastUpdate.With(prometheus.Labels{
			"uuid":    a.instanceUUID.String(),
			"name":    a.Outpost.Name,
			"version": constants.VERSION,
			"build":   constants.BUILD(),
		}).SetToCurrentTime()
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
		a.logger.Debug("Starting periodical timer...")
		a.startPeriodicalTasks()
	}()
	return nil
}
