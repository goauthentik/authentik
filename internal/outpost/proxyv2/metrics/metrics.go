package metrics

import (
	"net/http"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	Requests = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_requests",
		Help: "The total number of configured providers",
	}, []string{"method", "scheme", "path", "host", "type", "user"})
	UpstreamTiming = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "authentik_outpost_proxy_upstream_time",
		Help: "A summary of the duration we wait for the upstream reply",
	}, []string{"method", "scheme", "path", "host", "upstream_host", "user"})
)

func RunServer() {
	m := mux.NewRouter()
	m.HandleFunc("/akprox/ping", func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	m.Path("/metrics").Handler(promhttp.Handler())
	err := http.ListenAndServe("0.0.0.0:9300", m)
	if err != nil {
		panic(err)
	}
}
