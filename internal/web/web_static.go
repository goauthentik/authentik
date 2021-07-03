package web

import (
	"net/http"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	staticWeb "goauthentik.io/web"
)

func (ws *WebServer) configureStatic() {
	statRouter := ws.lh.NewRoute().Subrouter()
	// Media files, always local
	fs := http.FileServer(http.Dir(config.G.Paths.Media))
	if config.G.Debug || config.G.Web.LoadLocalFiles {
		ws.log.Debug("Using local static files")
		statRouter.PathPrefix("/static/dist").Handler(http.StripPrefix("/static/dist", http.FileServer(http.Dir("./web/dist"))))
		statRouter.PathPrefix("/static/authentik").Handler(http.StripPrefix("/static/authentik", http.FileServer(http.Dir("./web/authentik"))))
		statRouter.PathPrefix("/media").Handler(http.StripPrefix("/media", fs))
	} else {
		statRouter.Use(ws.staticHeaderMiddleware)
		ws.log.Debug("Using packaged static files with aggressive caching")
		statRouter.PathPrefix("/static/dist").Handler(http.StripPrefix("/static", http.FileServer(http.FS(staticWeb.StaticDist))))
		statRouter.PathPrefix("/static/authentik").Handler(http.StripPrefix("/static", http.FileServer(http.FS(staticWeb.StaticAuthentik))))
		statRouter.PathPrefix("/media").Handler(http.StripPrefix("/media", fs))
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
}

func (ws *WebServer) staticHeaderMiddleware(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "\"public, no-transform\"")
		w.Header().Set("X-authentik-version", constants.VERSION)
		w.Header().Set("Vary", "X-authentik-version")
		h.ServeHTTP(w, r)
	})
}
