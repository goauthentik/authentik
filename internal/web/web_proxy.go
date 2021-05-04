package web

import (
	"net/http"
	"net/http/httputil"
	"net/url"
)

func (ws *WebServer) configureProxy() {
	// Reverse proxy to the application server
	u, _ := url.Parse("http://localhost:8000")
	rp := httputil.NewSingleHostReverseProxy(u)
	rp.ErrorHandler = ws.proxyErrorHandler
	ws.m.PathPrefix("/").Handler(rp)
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	ws.log.WithError(err).Warning("proxy error")
	rw.WriteHeader(http.StatusBadGateway)
}
