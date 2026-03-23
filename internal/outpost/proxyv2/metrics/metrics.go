package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
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
)
