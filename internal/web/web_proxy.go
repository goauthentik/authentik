package web

import (
	"net/http"
	"net/http/httputil"
	"net/url"
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
	ws.m.PathPrefix("/").Handler(rp)
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	ws.log.WithError(err).Warning("proxy error")
	rw.WriteHeader(http.StatusBadGateway)
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("server", "authentik")
	return nil
}
