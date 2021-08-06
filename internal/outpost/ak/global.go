package ak

import (
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/constants"
)

func doGlobalSetup(config map[string]interface{}) {
	log.SetFormatter(&log.JSONFormatter{
		FieldMap: log.FieldMap{
			log.FieldKeyMsg:  "event",
			log.FieldKeyTime: "timestamp",
		},
	})
	switch config[ConfigLogLevel].(string) {
	case "trace":
		log.SetLevel(log.TraceLevel)
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
	log.WithField("buildHash", constants.BUILD()).WithField("version", constants.VERSION).Info("Starting authentik outpost")

	env := config[ConfigErrorReportingEnvironment].(string)
	var dsn string
	if config[ConfigErrorReportingEnabled].(bool) {
		dsn = "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8"
		log.WithField("env", env).Debug("Error reporting enabled")
	}

	err := sentry.Init(sentry.ClientOptions{
		Dsn:              dsn,
		Environment:      env,
		TracesSampleRate: 1,
	})
	if err != nil {
		log.Fatalf("sentry.Init: %s", err)
	}

	defer sentry.Flush(2 * time.Second)
}

// GetTLSTransport Get a TLS transport instance, that skips verification if configured via environment variables.
func GetTLSTransport() http.RoundTripper {
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
