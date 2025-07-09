package metrics

import (
	"net/http"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	Requests = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_request_duration_seconds",
		Help: "Proxy request latencies in seconds",
	}, []string{"outpost_name", "method", "host", "type"})
	UpstreamTiming = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_upstream_response_duration_seconds",
		Help: "Proxy upstream response latencies in seconds",
	}, []string{"outpost_name", "method", "scheme", "host", "upstream_host"})

	// Session store metrics
	SessionOperations = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "authentik_outpost_proxy_session_operations_total",
		Help: "Total number of session store operations",
	}, []string{"outpost_name", "operation", "backend"})

	SessionDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_session_operation_duration_seconds",
		Help: "Session store operation latencies in seconds",
	}, []string{"outpost_name", "operation", "backend"})

	SessionCleanupTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "authentik_outpost_proxy_session_cleanup_total",
		Help: "Total number of sessions cleaned up",
	}, []string{"outpost_name", "backend"})
)

func RunServer() {
	m := mux.NewRouter()
	l := log.WithField("logger", "authentik.outpost.metrics")
	m.Use(sentry.SentryNoSampleMiddleware)
	m.HandleFunc("/outpost.goauthentik.io/ping", func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	m.Path("/metrics").Handler(promhttp.Handler())
	listen := config.Get().Listen.Metrics
	l.WithField("listen", listen).Info("Starting Metrics server")
	err := http.ListenAndServe(listen, m)
	if err != nil {
		l.WithError(err).Warning("Failed to start metrics listener")
	}
}
