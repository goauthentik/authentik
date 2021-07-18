package ak

import (
	"context"
	"crypto/tls"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/getsentry/sentry-go"
	httptransport "github.com/go-openapi/runtime/client"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
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

// ParseCertificate Load certificate from Keyepair UUID and parse it into a go Certificate
func ParseCertificate(kpUuid string, cryptoApi *api.CryptoApiService) (*tls.Certificate, error) {
	cert, _, err := cryptoApi.CryptoCertificatekeypairsViewCertificateRetrieve(context.Background(), kpUuid).Execute()
	if err != nil {
		return nil, err
	}
	key, _, err := cryptoApi.CryptoCertificatekeypairsViewPrivateKeyRetrieve(context.Background(), kpUuid).Execute()
	if err != nil {
		return nil, err
	}

	x509cert, err := tls.X509KeyPair([]byte(cert.Data), []byte(key.Data))
	if err != nil {
		return nil, err
	}
	return &x509cert, nil
}
