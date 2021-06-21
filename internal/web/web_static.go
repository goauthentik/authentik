package web

import (
	"net/http"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	staticWeb "goauthentik.io/web"
)

func (ws *WebServer) configureStatic() {
	statRouter := ws.lh.NewRoute().Subrouter()
	if config.G.Debug || config.G.Web.LoadLocalFiles {
		ws.log.Debug("Using local static files")
		ws.lh.PathPrefix("/static/dist").Handler(http.StripPrefix("/static/dist", http.FileServer(http.Dir("./web/dist"))))
		ws.lh.PathPrefix("/static/authentik").Handler(http.StripPrefix("/static/authentik", http.FileServer(http.Dir("./web/authentik"))))
	} else {
		statRouter.Use(ws.staticHeaderMiddleware)
		ws.log.Debug("Using packaged static files with aggressive caching")
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
	// Media files, always local
	ws.lh.PathPrefix("/media").Handler(http.StripPrefix("/media", http.FileServer(http.Dir(config.G.Paths.Media))))
}

func (ws *WebServer) staticHeaderMiddleware(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "\"public, no-transform\"")
		w.Header().Set("X-authentik-version", constants.VERSION)
		w.Header().Set("Vary", "X-authentik-version")
		h.ServeHTTP(w, r)
	})
}
