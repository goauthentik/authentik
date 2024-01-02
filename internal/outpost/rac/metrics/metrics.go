package metrics

import (
	"net/http"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
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
