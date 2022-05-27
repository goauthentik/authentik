package proxyv2

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/application"
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
		"host":         web.GetHost(r),
		"type":         "ping",
	}).Observe(float64(after))
}

func (ps *ProxyServer) HandleStatic(rw http.ResponseWriter, r *http.Request) {
	before := time.Now()
	web.DisableIndex(http.StripPrefix("/outpost.goauthentik.io/static/dist", staticWeb.StaticHandler)).ServeHTTP(rw, r)
	after := time.Since(before)
	metrics.Requests.With(prometheus.Labels{
		"outpost_name": ps.akAPI.Outpost.Name,
		"method":       r.Method,
		"host":         web.GetHost(r),
		"type":         "static",
	}).Observe(float64(after))
}

func (ps *ProxyServer) lookupApp(r *http.Request) (*application.Application, string) {
	host := web.GetHost(r)
	// Try to find application by directly looking up host first (proxy, forward_auth_single)
	a, ok := ps.apps[host]
	if ok {
		ps.log.WithField("host", host).WithField("app", a.ProxyConfig().Name).Trace("Found app based direct host match")
		return a, host
	}
	// For forward_auth_domain, we don't have a direct app to domain relationship
	// Check through all apps, and check how much of their cookie domain matches the host
	// Return the application that has the longest match
	var longestMatch *application.Application
	longestMatchLength := 0
	for _, app := range ps.apps {
		if app.Mode() != api.PROXYMODE_FORWARD_DOMAIN {
			continue
		}
		// Check if the cookie domain has a leading period for a wildcard
		// This will decrease the weight of a wildcard domain, but a request to example.com
		// with the cookie domain set to example.com will still be routed correctly.
		cd := strings.TrimPrefix(*app.ProxyConfig().CookieDomain, ".")
		if !strings.HasSuffix(host, cd) {
			continue
		}
		if len(cd) < longestMatchLength {
			continue
		}
		longestMatch = app
		longestMatchLength = len(cd)
		// Also for forward_auth_domain, we need to respond on the external domain
		if app.ProxyConfig().ExternalHost == host {
			ps.log.WithField("host", host).WithField("app", app.ProxyConfig().Name).Debug("Found app based on external_host")
			return app, host
		}
	}
	// Check if our longes match is 0, in which case we didn't match, so we
	// manually return no app
	if longestMatchLength == 0 {
		return nil, host
	}
	ps.log.WithField("host", host).WithField("app", longestMatch.ProxyConfig().Name).Debug("Found app based on cookie domain")
	return longestMatch, host
}

func (ps *ProxyServer) Handle(rw http.ResponseWriter, r *http.Request) {
	if strings.HasPrefix(r.URL.Path, "/outpost.goauthentik.io/static") {
		ps.HandleStatic(rw, r)
		return
	}
	if strings.HasPrefix(r.URL.Path, "/outpost.goauthentik.io/ping") {
		ps.HandlePing(rw, r)
		return
	}
	a, host := ps.lookupApp(r)
	if a == nil {
		// If we only have one handler, host name switching doesn't matter
		if len(ps.apps) == 1 {
			ps.log.WithField("host", host).Trace("passing to single app mux")
			for k := range ps.apps {
				ps.apps[k].ServeHTTP(rw, r)
				return
			}
		}

		ps.log.WithField("headers", r.Header).Trace("tracing headers for no hostname match")
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
