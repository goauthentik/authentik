package ak

import (
	"context"
	"fmt"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/utils/web"

	log "github.com/sirupsen/logrus"
)

type WSHandler func(ctx context.Context, args map[string]interface{})

const ConfigLogLevel = "log_level"

// APIController main controller which connects to the authentik api via http and ws
type APIController struct {
	Client       *api.APIClient
	Outpost      api.Outpost
	GlobalConfig *api.Config

	Server Outpost

	token string

	logger *log.Entry

	reloadOffset time.Duration

	wsConn              *websocket.Conn
	lastWsReconnect     time.Time
	wsIsReconnecting    bool
	wsBackoffMultiplier int
	wsHandlers          []WSHandler
	refreshHandlers     []func()

	instanceUUID uuid.UUID
}

// NewAPIController initialise new API Controller instance from URL and API token
func NewAPIController(akURL url.URL, token string) *APIController {
	rsp := sentry.StartSpan(context.Background(), "authentik.outposts.init")

	config := api.NewConfiguration()
	config.Host = akURL.Host
	config.Scheme = akURL.Scheme
	config.HTTPClient = &http.Client{
		Transport: web.NewUserAgentTransport(
			constants.OutpostUserAgent(),
			web.NewTracingTransport(
				rsp.Context(),
				GetTLSTransport(),
			),
		),
	}
	config.AddDefaultHeader("Authorization", fmt.Sprintf("Bearer %s", token))

	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	log := log.WithField("logger", "authentik.outpost.ak-api-controller")

	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, _, err := apiClient.OutpostsApi.OutpostsInstancesList(context.Background()).Execute()

	if err != nil {
		log.WithError(err).Error("Failed to fetch outpost configuration, retrying in 3 seconds")
		time.Sleep(time.Second * 3)
		return NewAPIController(akURL, token)
	}
	if len(outposts.Results) < 1 {
		panic("No outposts found with given token, ensure the given token corresponds to an authenitk Outpost")
	}
	outpost := outposts.Results[0]

	log.WithField("name", outpost.Name).Debug("Fetched outpost configuration")

	akConfig, _, err := apiClient.RootApi.RootConfigRetrieve(context.Background()).Execute()
	if err != nil {
		log.WithError(err).Error("Failed to fetch global configuration")
		return nil
	}
	log.Debug("Fetched global configuration")

	// doGlobalSetup is called by the OnRefresh handler, which ticks on start
	// doGlobalSetup(outpost, akConfig)

	ac := &APIController{
		Client:       apiClient,
		GlobalConfig: akConfig,

		token:  token,
		logger: log,

		reloadOffset:        time.Duration(rand.Intn(10)) * time.Second,
		instanceUUID:        uuid.New(),
		Outpost:             outpost,
		wsHandlers:          []WSHandler{},
		wsBackoffMultiplier: 1,
		refreshHandlers:     make([]func(), 0),
	}
	ac.logger.WithField("offset", ac.reloadOffset.String()).Debug("HA Reload offset")
	err = ac.initWS(akURL, outpost.Pk)
	if err != nil {
		go ac.reconnectWS()
	}
	ac.configureRefreshSignal()
	return ac
}

// Start Starts all handlers, non-blocking
func (a *APIController) Start() error {
	err := a.Server.Refresh()
	if err != nil {
		return err
	}
	err = a.StartBackgroundTasks()
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

func (a *APIController) configureRefreshSignal() {
	s := make(chan os.Signal, 1)
	go func() {
		for {
			<-s
			err := a.OnRefresh()
			if err != nil {
				a.logger.WithError(err).Warning("failed to refresh")
			}
		}
	}()
	signal.Notify(s, syscall.SIGUSR1)
	a.logger.Debug("Enabled USR1 hook to reload")
}

func (a *APIController) AddRefreshHandler(handler func()) {
	a.refreshHandlers = append(a.refreshHandlers, handler)
}

func (a *APIController) AddWSHandler(handler WSHandler) {
	a.wsHandlers = append(a.wsHandlers, handler)
}

func (a *APIController) OnRefresh() error {
	// Because we don't know the outpost UUID, we simply do a list and pick the first
	// The service account this token belongs to should only have access to a single outpost
	outposts, _, err := a.Client.OutpostsApi.OutpostsInstancesList(context.Background()).Execute()

	if err != nil {
		log.WithError(err).Error("Failed to fetch outpost configuration")
		return err
	}
	a.Outpost = outposts.Results[0]

	a.logger.WithField("name", a.Outpost.Name).Debug("Fetched outpost configuration")
	doGlobalSetup(a.Outpost, a.GlobalConfig)
	err = a.Server.Refresh()
	for _, handler := range a.refreshHandlers {
		handler()
	}
	return err
}

func (a *APIController) getWebsocketArgs() map[string]interface{} {
	args := map[string]interface{}{
		"version":   constants.VERSION,
		"buildHash": constants.BUILD("tagged"),
		"uuid":      a.instanceUUID.String(),
	}
	hostname, err := os.Hostname()
	if err == nil {
		args["hostname"] = hostname
	}
	return args
}

func (a *APIController) StartBackgroundTasks() error {
	OutpostInfo.With(prometheus.Labels{
		"outpost_name": a.Outpost.Name,
		"outpost_type": a.Server.Type(),
		"uuid":         a.instanceUUID.String(),
		"version":      constants.VERSION,
		"build":        constants.BUILD("tagged"),
	}).Set(1)
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
