package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
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
)
