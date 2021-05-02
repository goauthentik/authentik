package web

import (
	"net/http/httputil"
	"net/url"
)

func (ws *WebServer) configureProxy() {
	// Reverse proxy to the application server
	u, _ := url.Parse("http://localhost:8000")
	rp := httputil.NewSingleHostReverseProxy(u)
	ws.m.PathPrefix("/").Handler(rp)
}
