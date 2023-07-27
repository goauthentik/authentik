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

	// NOTE: the following metric is kept for compatibility purpose
	RequestsLegacy = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_requests",
		Help: "The total number of configured providers",
	}, []string{"outpost_name", "method", "host", "type"})
	UpstreamTimingLegacy = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_upstream_time",
		Help: "A summary of the duration we wait for the upstream reply",
	}, []string{"outpost_name", "method", "scheme", "host", "upstream_host"})
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
