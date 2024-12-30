package ak

import (
	"fmt"
	"net/http"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
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
	l := config.Get().Logger().Named("authentik.outpost")
	m := outpost.Managed.Get()
	level, ok := outpost.Config[ConfigLogLevel]
	if !ok {
		level = "info"
	}
	var pl zapcore.Level
	if m == nil || *m == "" {
		switch level.(string) {
		case "trace":
			pl = zapcore.DebugLevel
		case "debug":
			pl = zapcore.DebugLevel
		case "info":
			pl = zapcore.InfoLevel
		case "warning":
			pl = zapcore.WarnLevel
		case "error":
			pl = zapcore.ErrorLevel
		default:
			pl = zapcore.DebugLevel
		}
	} else {
		l.Debug("Managed outpost, not setting global log level")
	}
	nl := config.Get().BuildLoggerWithLevel(pl)
	config.Get().SetLogger(nl)

	if globalConfig.ErrorReporting.Enabled {
		if !initialSetup {
			l.Debug("Error reporting enabled", zap.String("env", globalConfig.ErrorReporting.Environment))
		}
		err := sentry.Init(sentry.ClientOptions{
			Dsn:           globalConfig.ErrorReporting.SentryDsn,
			Environment:   globalConfig.ErrorReporting.Environment,
			EnableTracing: true,
			TracesSampler: sentryutils.SamplerFunc(float64(globalConfig.ErrorReporting.TracesSampleRate)),
			Release:       fmt.Sprintf("authentik@%s", constants.VERSION),
			HTTPTransport: webutils.NewUserAgentTransport(constants.OutpostUserAgent(), http.DefaultTransport),
			IgnoreErrors: []string{
				http.ErrAbortHandler.Error(),
			},
		})
		if err != nil {
			l.Warn("Failed to initialise sentry", zap.Error(err), zap.String("env", globalConfig.ErrorReporting.Environment))
		}
	}

	if !initialSetup {
		l.Info("Starting authentik outpost", zap.String("hash", constants.BUILD("tagged")), zap.String("version", constants.VERSION))
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
