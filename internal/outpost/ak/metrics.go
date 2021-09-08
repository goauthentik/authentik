package ak

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	OutpostInfo = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_info",
		Help: "Outpost info",
	}, []string{"uuid", "name", "version", "build"})
	LastUpdate = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_last_update",
		Help: "Time of last update",
	}, []string{"uuid", "name", "version", "build"})
	ConnectionStatus = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "authentik_outpost_connection",
		Help: "Connection status",
	}, []string{"uuid", "name"})
)
