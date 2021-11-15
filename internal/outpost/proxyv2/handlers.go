package proxyv2

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
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
		"scheme":       r.URL.Scheme,
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
		"scheme":       r.URL.Scheme,
		"path":         r.URL.Path,
		"host":         web.GetHost(r),
		"type":         "ping",
		"user":         "",
	}).Observe(float64(after))
}

func (ps *ProxyServer) Handle(rw http.ResponseWriter, r *http.Request) {
	if strings.HasPrefix(r.URL.Path, "/akprox/static") {
		ps.HandleStatic(rw, r)
		return
	}
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

		rw.Header().Set("Content-Type", "application/json")
		rw.WriteHeader(http.StatusBadRequest)
		j := json.NewEncoder(rw)
		j.SetIndent("", "\t")
		err := j.Encode(struct {
			Message string
			Host    string
			Detail  string
		}{
			Message: "no app for hostname",
			Host:    host,
			Detail:  fmt.Sprintf("Check the outpost settings and make sure '%s' is included.", host),
		})
		if err != nil {
			ps.log.WithError(err).Warning("Failed to write error body")
		}
		return
	}
	ps.log.WithField("host", host).Trace("passing to application mux")
	a.ServeHTTP(rw, r)
}
