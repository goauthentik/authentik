package ak

import (
	"encoding/base64"
	"fmt"
	"math/rand"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
)

func TestSecret() string {
	return base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
}

func MockConfig() api.Config {
	return *api.NewConfig(
		*api.NewErrorReportingConfig(false, "test", false, 0.0),
		[]api.CapabilitiesEnum{},
		100,
		100,
		100,
		100,
	)
}

func MockAK(outpost api.Outpost, globalConfig api.Config) *APIController {
	config := api.NewConfiguration()
	config.HTTPClient = &http.Client{
		Transport: GetTLSTransport(),
	}
	token := TestSecret()
	config.AddDefaultHeader("Authorization", fmt.Sprintf("Bearer %s", token))

	// create the API client, with the transport
	apiClient := api.NewAPIClient(config)

	log := log.WithField("logger", "authentik.outpost.ak-api-controller")

	log.WithField("name", outpost.Name).Debug("Fetched outpost configuration")

	log.Debug("Fetched global configuration")

	// doGlobalSetup is called by the OnRefresh handler, which ticks on start
	// doGlobalSetup(outpost, akConfig)

	ac := &APIController{
		Client:       apiClient,
		GlobalConfig: &globalConfig,

		token:  token,
		logger: log,

		reloadOffset:        time.Duration(rand.Intn(10)) * time.Second,
		instanceUUID:        uuid.New(),
		Outpost:             outpost,
		wsBackoffMultiplier: 1,
		refreshHandlers:     make([]func(), 0),
	}
	ac.logger.WithField("offset", ac.reloadOffset.String()).Debug("HA Reload offset")
	return ac
}
