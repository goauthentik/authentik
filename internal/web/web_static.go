package web

import (
	"net/http"

	"goauthentik.io/internal/config"
	staticWeb "goauthentik.io/web"
)

func (ws *WebServer) configureStatic() {
	if config.G.Debug {
		ws.log.Debug("Using local static files")
		ws.lh.PathPrefix("/static/dist").Handler(http.StripPrefix("/static/dist", http.FileServer(http.Dir("./web/dist"))))
		ws.lh.PathPrefix("/static/authentik").Handler(http.StripPrefix("/static/authentik", http.FileServer(http.Dir("./web/authentik"))))
	} else {
		ws.log.Debug("Using packaged static files")
		ws.lh.PathPrefix("/static/dist").Handler(http.StripPrefix("/static", http.FileServer(http.FS(staticWeb.StaticDist))))
		ws.lh.PathPrefix("/static/authentik").Handler(http.StripPrefix("/static", http.FileServer(http.FS(staticWeb.StaticAuthentik))))
	}
	ws.lh.Path("/robots.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		rw.Write(staticWeb.RobotsTxt)
	})
	ws.lh.Path("/.well-known/security.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		rw.Write(staticWeb.SecurityTxt)
	})
	// Interfaces
	ws.lh.Path("/if/admin/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/html"}
		rw.WriteHeader(200)
		rw.Write(staticWeb.InterfaceAdmin)
	})
	ws.lh.Path("/if/flow/{slug}/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/html"}
		rw.WriteHeader(200)
		rw.Write(staticWeb.InterfaceFlow)
	})
	// Media files, always local
	ws.lh.PathPrefix("/media").Handler(http.StripPrefix("/media", http.FileServer(http.Dir(config.G.Paths.Media))))
}
