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
		Name: "authentik_outpost_ldap_requests",
		Help: "The total number of configured providers",
	}, []string{"outpost_name", "type", "dn", "filter", "client"})
	RequestsRejected = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "authentik_outpost_ldap_requests_rejected",
		Help: "Total number of rejected requests",
	}, []string{"outpost_name", "type", "reason", "dn", "client"})
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
