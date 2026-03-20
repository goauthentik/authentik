package web

import (
	"fmt"
	"net/http"
	"os"
	"path"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"
	"goauthentik.io/internal/utils/unix"
)

var Requests = promauto.NewHistogramVec(prometheus.HistogramOpts{
	Name: "authentik_main_request_duration_seconds",
	Help: "API request latencies in seconds",
}, []string{"dest"})

func (ws *WebServer) runMetricsServer() {
	l := log.WithField("logger", "authentik.router.metrics")

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
			l.WithError(err).Warning("failed to get upstream metrics")
			return
		}
		_, err = ws.upstreamHttpClient().Do(re)
		if err != nil {
			l.WithError(err).Warning("failed to get upstream metrics")
			return
		}
	})
	socketPath := path.Join(os.TempDir(), "authentik-server-metrics.sock")
	l = l.WithField("listen", socketPath)
	l.Info("Starting Metrics server")
	ln, err := unix.Listen(socketPath)
	if err != nil {
		l.WithError(err).Warning("failed to listen")
	}
	defer func() {
		err := ln.Close()
		if err != nil {
			l.WithError(err).Warning("failed to close listener")
		}
	}()
	err = http.Serve(ln, m)
	if err != nil {
		l.WithError(err).Warning("Failed to start metrics server")
	}
	l.Info("Stopping Metrics server")
}
