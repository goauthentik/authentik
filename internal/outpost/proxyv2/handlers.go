package proxyv2

import (
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/utils/web"
	staticWeb "goauthentik.io/web"
)

func (ps *ProxyServer) HandlePing(rw http.ResponseWriter, r *http.Request) {
	before := time.Now()
	rw.WriteHeader(204)
	after := time.Since(before)
	metrics.Requests.With(prometheus.Labels{
		"outpost_name": ps.akAPI.Outpost.Name,
		"method":       r.Method,
		"schema":       r.URL.Scheme,
		"path":         r.URL.Path,
		"host":         web.GetHost(r),
		"type":         "ping",
		"user":         "",
	}).Observe(float64(after))
}

func (ps *ProxyServer) HandleStatic(rw http.ResponseWriter, r *http.Request) {
	staticFs := http.FileServer(http.FS(staticWeb.StaticDist))
	before := time.Now()
	http.StripPrefix("/akprox/static", staticFs).ServeHTTP(rw, r)
	after := time.Since(before)
	metrics.Requests.With(prometheus.Labels{
		"outpost_name": ps.akAPI.Outpost.Name,
		"method":       r.Method,
		"schema":       r.URL.Scheme,
		"path":         r.URL.Path,
		"host":         web.GetHost(r),
		"type":         "ping",
		"user":         "",
	}).Observe(float64(after))
}

func (ps *ProxyServer) Handle(rw http.ResponseWriter, r *http.Request) {
	host := web.GetHost(r)
	a, ok := ps.apps[host]
	if !ok {
		// If we only have one handler, host name switching doesn't matter
		if len(ps.apps) == 1 {
			ps.log.WithField("host", host).Warning("passing to single app mux")
			for k := range ps.apps {
				ps.apps[k].ServeHTTP(rw, r)
				return
			}
		}

		ps.log.WithField("host", host).Warning("no app for hostname")
		rw.WriteHeader(400)
		return
	}
	ps.log.WithField("host", host).Trace("passing to application mux")
	a.ServeHTTP(rw, r)
}
