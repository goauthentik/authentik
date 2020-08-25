package cmd

import (
	"math/rand"
	"net/url"
	"os"
	"os/signal"
	"time"

	"github.com/BeryJu/passbook/proxy/pkg/client"
	"github.com/BeryJu/passbook/proxy/pkg/client/root"
	"github.com/BeryJu/passbook/proxy/pkg/server"
	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	"github.com/go-openapi/strfmt"

	log "github.com/sirupsen/logrus"
)

// RunServer main entrypoint, runs the full server
func RunServer() {
	pbURL, found := os.LookupEnv("PASSBOOK_HOST")
	if !found {
		panic("env PASSBOOK_HOST not set!")
	}
	pbToken, found := os.LookupEnv("PASSBOOK_TOKEN")
	if !found {
		panic("env PASSBOOK_TOKEN not set!")
	}

	pbURLActual, err := url.Parse(pbURL)
	if err != nil {
		panic(err)
	}

	// create the transport
	transport := httptransport.New(pbURLActual.Host, client.DefaultBasePath, []string{pbURLActual.Scheme})
	basicAuth := httptransport.BasicAuth("", pbToken)

	// create the API client, with the transport
	apiClient := client.New(transport, strfmt.Default)

	rand.Seed(time.Now().UnixNano())

	// Get configuration from passbook server
	config, err := apiClient.Root.RootConfigList(root.NewRootConfigListParams(), basicAuth)
	if err != nil {
		panic(err)
	}
	log.Debugf("Got config from pb: %+v", config.Payload[0])

	switch config.Payload[0].LogLevel {
	case "debug":
		log.SetLevel(log.DebugLevel)
	case "info":
		log.SetLevel(log.InfoLevel)
	case "warning":
		log.SetLevel(log.WarnLevel)
	case "error":
		log.SetLevel(log.ErrorLevel)
	default:
		log.SetLevel(log.DebugLevel)
	}

	var dsn string
	if *config.Payload[0].ErrorReportingEnabled {
		dsn = "https://33cdbcb23f8b436dbe0ee06847410b67@sentry.beryju.org/3"
		log.Debug("Error reporting enabled")
	}

	err = sentry.Init(sentry.ClientOptions{
		Dsn:         dsn,
		Environment: config.Payload[0].ErrorReportingEnvironment,
	})
	if err != nil {
		log.Fatalf("sentry.Init: %s", err)
	}

	defer sentry.Flush(2 * time.Second)

	ac := server.NewAPIController(*pbURLActual, pbToken)

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	ac.Start()

	for {
		select {
		case <-interrupt:
			ac.Shutdown()
			os.Exit(0)
		}
	}
}
