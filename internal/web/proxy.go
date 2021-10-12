package web

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/utils/web"
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
	}
	rp := &httputil.ReverseProxy{Director: director}
	rp.ErrorHandler = ws.proxyErrorHandler
	rp.ModifyResponse = ws.proxyModifyResponse
	ws.m.PathPrefix("/akprox").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		if ws.ProxyServer != nil {
			before := time.Now()
			ws.ProxyServer.Handle(rw, r)
			Requests.With(prometheus.Labels{
				"dest": "embedded_outpost",
			}).Observe(float64(time.Since(before)))
			return
		}
		ws.proxyErrorHandler(rw, r, fmt.Errorf("proxy not running"))
	})
	ws.m.Path("/-/health/live/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	ws.m.PathPrefix("/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		if !ws.p.IsRunning() {
			ws.proxyErrorHandler(rw, r, fmt.Errorf("authentik core not running yet"))
			return
		}
		host := web.GetHost(r)
		before := time.Now()
		if ws.ProxyServer != nil {
			if ws.ProxyServer.HandleHost(host, rw, r) {
				Requests.With(prometheus.Labels{
					"dest": "embedded_outpost",
				}).Observe(float64(time.Since(before)))
				return
			}
		}
		Requests.With(prometheus.Labels{
			"dest": "py",
		}).Observe(float64(time.Since(before)))
		ws.log.WithField("host", host).Trace("routing to application server")
		rp.ServeHTTP(rw, r)
	})
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	ws.log.Warning(err.Error())
	rw.WriteHeader(http.StatusBadGateway)
	_, err = rw.Write([]byte("authentik starting..."))
	if err != nil {
		ws.log.WithError(err).Warning("failed to write error message")
	}
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("server", "authentik")
	return nil
}
