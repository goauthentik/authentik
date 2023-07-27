package web

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/utils/sentry"
)

func (ws *WebServer) configureProxy() {
	// Reverse proxy to the application server
	u, _ := url.Parse("http://localhost:8000")
	director := func(req *http.Request) {
		req.URL.Scheme = u.Scheme
		req.URL.Host = u.Host
		if _, ok := req.Header["User-Agent"]; !ok {
			// explicitly disable User-Agent so it's not set to default value
			req.Header.Set("User-Agent", "")
		}
		if req.TLS != nil {
			req.Header.Set("X-Forwarded-Proto", "https")
		}
		ws.log.WithField("url", req.URL.String()).WithField("headers", req.Header).Trace("tracing request to backend")
	}
	rp := &httputil.ReverseProxy{Director: director}
	rp.ErrorHandler = ws.proxyErrorHandler
	rp.ModifyResponse = ws.proxyModifyResponse
	ws.m.PathPrefix("/outpost.goauthentik.io").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		if ws.ProxyServer != nil {
			before := time.Now()
			ws.ProxyServer.Handle(rw, r)
			elapsed := time.Since(before)
			Requests.With(prometheus.Labels{
				"dest": "embedded_outpost",
			}).Observe(float64(elapsed) / float64(time.Second))
			RequestsLegacy.With(prometheus.Labels{
				"dest": "embedded_outpost",
			}).Observe(float64(elapsed))
			return
		}
		ws.proxyErrorHandler(rw, r, fmt.Errorf("proxy not running"))
	})
	ws.m.Path("/-/health/live/").HandlerFunc(sentry.SentryNoSample(func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	}))
	ws.m.PathPrefix("/").HandlerFunc(sentry.SentryNoSample(func(rw http.ResponseWriter, r *http.Request) {
		if !ws.p.IsRunning() {
			ws.proxyErrorHandler(rw, r, fmt.Errorf("authentik core not running yet"))
			return
		}
		before := time.Now()
		if ws.ProxyServer != nil {
			if ws.ProxyServer.HandleHost(rw, r) {
				elapsed := time.Since(before)
				Requests.With(prometheus.Labels{
					"dest": "embedded_outpost",
				}).Observe(float64(elapsed) / float64(time.Second))
				RequestsLegacy.With(prometheus.Labels{
					"dest": "embedded_outpost",
				}).Observe(float64(elapsed))
				return
			}
		}
		elapsed := time.Since(before)
		Requests.With(prometheus.Labels{
			"dest": "core",
		}).Observe(float64(elapsed) / float64(time.Second))
		RequestsLegacy.With(prometheus.Labels{
			"dest": "core",
		}).Observe(float64(elapsed))
		r.Body = http.MaxBytesReader(rw, r.Body, 32*1024*1024)
		rp.ServeHTTP(rw, r)
	}))
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	ws.log.WithError(err).Warning("failed to proxy to backend")
	rw.WriteHeader(http.StatusBadGateway)
	em := fmt.Sprintf("failed to connect to authentik backend: %v", err)
	if !ws.p.IsRunning() {
		em = "authentik starting..."
	}
	// return json if the client asks for json
	if req.Header.Get("Accept") == "application/json" {
		eem, _ := json.Marshal(map[string]string{
			"error": em,
		})
		em = string(eem)
	}
	_, err = rw.Write([]byte(em))
	if err != nil {
		ws.log.WithError(err).Warning("failed to write error message")
	}
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("X-Powered-By", "authentik")
	r.Header.Del("Server")
	return nil
}
