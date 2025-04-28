package ak

import (
	"fmt"
	"net/http"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	sentryutils "goauthentik.io/internal/utils/sentry"
	webutils "goauthentik.io/internal/utils/web"
)

var (
	initialSetup                    = false
	tlsTransport *http.RoundTripper = nil
)

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
		if !initialSetup {
			l.WithField("env", globalConfig.ErrorReporting.Environment).Debug("Error reporting enabled")
		}
		err := sentry.Init(sentry.ClientOptions{
			Dsn:           globalConfig.ErrorReporting.SentryDsn,
			Environment:   globalConfig.ErrorReporting.Environment,
			EnableTracing: true,
			TracesSampler: sentryutils.SamplerFunc(float64(globalConfig.ErrorReporting.TracesSampleRate)),
			Release:       fmt.Sprintf("authentik@%s", constants.VERSION),
			HTTPTransport: webutils.NewUserAgentTransport(constants.UserAgentOutpost(), http.DefaultTransport),
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
	if tlsTransport != nil {
		return *tlsTransport
	}
	tmp, err := httptransport.TLSTransport(httptransport.TLSClientOptions{
		InsecureSkipVerify: config.Get().AuthentikInsecure,
	})
	if err != nil {
		panic(err)
	}
	tlsTransport = &tmp
	return *tlsTransport
}
