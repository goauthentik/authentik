package ak

import (
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/outpost/pkg"
)

func doGlobalSetup(config map[string]interface{}) {
	log.SetFormatter(&log.JSONFormatter{})
	switch config[ConfigLogLevel].(string) {
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
	log.WithField("version", pkg.VERSION).Info("Starting authentik proxy")

	var dsn string
	if config[ConfigErrorReportingEnabled].(bool) {
		dsn = "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8"
		log.Debug("Error reporting enabled")
	}

	err := sentry.Init(sentry.ClientOptions{
		Dsn:         dsn,
		Environment: config[ConfigErrorReportingEnvironment].(string),
	})
	if err != nil {
		log.Fatalf("sentry.Init: %s", err)
	}

	defer sentry.Flush(2 * time.Second)
}

func getTLSTransport() http.RoundTripper {
	value, set := os.LookupEnv("AUTHENTIK_INSECURE")
	if !set {
		value = "false"
	}
	tlsTransport, err := httptransport.TLSTransport(httptransport.TLSClientOptions{
		InsecureSkipVerify: strings.ToLower(value) == "true",
	})
	if err != nil {
		panic(err)
	}
	return tlsTransport
}
