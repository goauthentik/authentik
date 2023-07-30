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
		Name: "authentik_outpost_ldap_request_duration_seconds",
		Help: "LDAP request latencies in seconds",
	}, []string{"outpost_name", "type", "app"})
	RequestsRejected = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "authentik_outpost_ldap_requests_rejected_total",
		Help: "Total number of rejected requests",
	}, []string{"outpost_name", "type", "reason", "app"})

	// NOTE: the following metrics are kept for compatibility purpose
	RequestsLegacy = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_ldap_requests",
		Help: "The total number of configured providers",
	}, []string{"outpost_name", "type", "app"})
	RequestsRejectedLegacy = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "authentik_outpost_ldap_requests_rejected",
		Help: "Total number of rejected requests",
	}, []string{"outpost_name", "type", "reason", "app"})
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
