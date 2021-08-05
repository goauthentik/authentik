package web

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"

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
			ws.ProxyServer.Handler(rw, r)
			return
		}
		ws.proxyErrorHandler(rw, r, fmt.Errorf("proxy not running"))
	})
	ws.m.PathPrefix("/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		host := web.GetHost(r)
		if ws.ProxyServer != nil {
			if _, ok := ws.ProxyServer.Handlers[host]; ok {
				ws.log.WithField("host", host).Trace("routing to proxy outpost")
				ws.ProxyServer.Handler(rw, r)
				return
			}
		}
		ws.log.WithField("host", host).Trace("routing to application server")
		rp.ServeHTTP(rw, r)
	})
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	ws.log.WithError(err).Warning("proxy error")
	rw.WriteHeader(http.StatusBadGateway)
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("server", "authentik")
	return nil
}
