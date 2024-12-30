package web

import (
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"

	"github.com/gorilla/mux"
	"github.com/gorilla/securecookie"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"
)

const MetricsKeyFile = "authentik-core-metrics.key"

var Requests = promauto.NewHistogramVec(prometheus.HistogramOpts{
	Name: "authentik_main_request_duration_seconds",
	Help: "API request latencies in seconds",
}, []string{"dest"})

func (ws *WebServer) runMetricsServer() {
	l := ws.log.Named("authentik.router.metrics")
	tmp := os.TempDir()
	key := base64.StdEncoding.EncodeToString(securecookie.GenerateRandomKey(64))
	keyPath := path.Join(tmp, MetricsKeyFile)
	err := os.WriteFile(keyPath, []byte(key), 0o600)
	if err != nil {
		l.Warn("failed to save metrics key", zap.Error(err))
		return
	}

	m := mux.NewRouter()
	m.Use(sentry.SentryNoSampleMiddleware)
	m.Path("/metrics").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		promhttp.InstrumentMetricHandler(
			prometheus.DefaultRegisterer, promhttp.HandlerFor(prometheus.DefaultGatherer, promhttp.HandlerOpts{
				DisableCompression: true,
			}),
		).ServeHTTP(rw, r)

		// Get upstream metrics
		re, err := http.NewRequest("GET", fmt.Sprintf("%s%s-/metrics/", ws.upstreamURL.String(), config.Get().Web.Path), nil)
		if err != nil {
			l.Warn("failed to get upstream metrics", zap.Error(err))
			return
		}
		re.Header.Set("Authorization", fmt.Sprintf("Bearer %s", key))
		res, err := ws.upstreamHttpClient().Do(re)
		if err != nil {
			l.Warn("failed to get upstream metrics", zap.Error(err))
			return
		}
		_, err = io.Copy(rw, res.Body)
		if err != nil {
			l.Warn("failed to get upstream metrics", zap.Error(err))
			return
		}
	})
	defer func() {
		err = os.Remove(keyPath)
		if err != nil {
			l.Warn("failed to remove metrics key file", zap.Error(err))
		}
	}()
	l.Info("Starting Metrics server", zap.String("listen", config.Get().Listen.Metrics))
	err = http.ListenAndServe(config.Get().Listen.Metrics, m)
	if err != nil {
		l.Warn("Failed to start metrics server", zap.Error(err))
		return
	}
	l.Info("Stopping Metrics server", zap.String("listen", config.Get().Listen.Metrics))
}
