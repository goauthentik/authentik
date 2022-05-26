package ak

import (
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/constants"
)

var initialSetup = false

func doGlobalSetup(outpost api.Outpost, globalConfig *api.Config) {
	l := log.WithField("logger", "authentik.outpost")
	m := outpost.Managed.Get()
	level, ok := outpost.Config[ConfigLogLevel]
	if !ok {
		level = "info"
	}
	if m == nil || *m == "" {
		switch level.(string) {
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
	} else {
		l.Debug("Managed outpost, not setting global log level")
	}

	if globalConfig.ErrorReporting.Enabled {
		dsn := "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8"
		if !initialSetup {
			l.WithField("env", globalConfig.ErrorReporting.Environment).Debug("Error reporting enabled")
		}
		err := sentry.Init(sentry.ClientOptions{
			Dsn:              dsn,
			Environment:      globalConfig.ErrorReporting.Environment,
			TracesSampleRate: float64(globalConfig.ErrorReporting.TracesSampleRate),
			Release:          fmt.Sprintf("authentik@%s", constants.VERSION),
			IgnoreErrors: []string{
				http.ErrAbortHandler.Error(),
			},
		})
		if err != nil {
			l.WithField("env", globalConfig.ErrorReporting.Environment).WithError(err).Warning("Failed to initialise sentry")
		}
	}

	if !initialSetup {
		l.WithField("hash", constants.BUILD("tagged")).WithField("version", constants.VERSION).Info("Starting authentik outpost")
		initialSetup = true
	}
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
