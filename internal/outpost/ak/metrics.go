package ak

import (
	"net/http"
	"os"
	"path"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/utils/sentry"
	"goauthentik.io/internal/utils/unix"
)

var (
	MetricsSocketName = "authentik-metrics.sock"
	OutpostInfo       = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_info",
		Help: "Outpost info",
	}, []string{"outpost_name", "outpost_type", "uuid", "version", "build"})
	LastUpdate = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_last_update",
		Help: "Time of last update",
	}, []string{"outpost_name", "outpost_type", "uuid", "version", "build"})
	ConnectionStatus = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_connection",
		Help: "Connection status",
	}, []string{"outpost_name", "outpost_type", "uuid"})
)

func MetricsRouter() *mux.Router {
	m := mux.NewRouter()
	m.Use(sentry.SentryNoSampleMiddleware)
	m.HandleFunc("/outpost.goauthentik.io/ping", func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	m.Path("/metrics").Handler(promhttp.Handler())
	return m
}

func RunMetricsServer(listen string, router *mux.Router) {
	l := log.WithField("logger", "authentik.outpost.metrics").WithField("listen", listen)
	l.Info("Starting Metrics server")
	err := http.ListenAndServe(listen, router)
	if err != nil {
		l.WithError(err).Warning("Failed to start metrics listener")
	}
}

func RunMetricsUnix(router *mux.Router) {
	socketPath := path.Join(os.TempDir(), MetricsSocketName)
	_ = os.Remove(socketPath)
	l := log.WithField("logger", "authentik.outpost.metrics").WithField("listen", socketPath)
	ln, err := unix.Listen(socketPath)
	if err != nil {
		l.WithError(err).Warning("failed to listen")
		return
	}
	defer func() {
		err := ln.Close()
		_ = os.Remove(socketPath)
		if err != nil {
			l.WithError(err).Warning("failed to close listener")
		}
	}()
	l.WithField("listen", socketPath).Info("Starting Metrics server")
	err = http.Serve(ln, router)
	if err != nil {
		l.WithError(err).Warning("Failed to start metrics listener")
	}
}
