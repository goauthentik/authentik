package web

import (
	"fmt"
	"net/http"

	"github.com/go-http-utils/etag"
	"github.com/gorilla/mux"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/utils/web"
	staticWeb "goauthentik.io/web"
)

func (ws *WebServer) configureStatic() {
	// Setup routers
	staticRouter := ws.loggingRouter.NewRoute().Subrouter()
	staticRouter.Use(ws.staticHeaderMiddleware)
	indexLessRouter := staticRouter.NewRoute().Subrouter()
	// Specifically disable index
	indexLessRouter.Use(web.DisableIndex)

	distFs := http.FileServer(http.Dir("./web/dist"))

	pathStripper := func(handler http.Handler, paths ...string) http.Handler {
		h := handler
		for _, path := range paths {
			h = http.StripPrefix(path, h)
		}
		return h
	}

	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/dist/").Handler(pathStripper(
		distFs,
		"static/dist/",
		config.Get().Web.Path,
	))
	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/authentik/").Handler(pathStripper(
		http.FileServer(http.Dir("./web/authentik")),
		"static/authentik/",
		config.Get().Web.Path,
	))

	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/flow/"+vars["flow_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})
	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/admin/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/admin", config.Get().Web.Path), distFs))
	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/user/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/user", config.Get().Web.Path), distFs))
	indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/rac/{app_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/rac/"+vars["app_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})

	// Media files, if backend is file
	if config.Get().Storage.Media.Backend == "file" {
		fsMedia := http.FileServer(http.Dir(config.Get().Storage.Media.File.Path))
		indexLessRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/media/").Handler(pathStripper(
			http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
				fsMedia.ServeHTTP(w, r)
			}),
			"media/",
			config.Get().Web.Path,
		))
	}

	staticRouter.PathPrefix(config.Get().Web.Path).Path("/robots.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		_, err := rw.Write(staticWeb.RobotsTxt)
		if err != nil {
			ws.log.WithError(err).Warning("failed to write response")
		}
	})
	staticRouter.PathPrefix(config.Get().Web.Path).Path("/.well-known/security.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		_, err := rw.Write(staticWeb.SecurityTxt)
		if err != nil {
			ws.log.WithError(err).Warning("failed to write response")
		}
	})
}

func (ws *WebServer) staticHeaderMiddleware(h http.Handler) http.Handler {
	etagHandler := etag.Handler(h, false)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "public, no-transform")
		w.Header().Set("X-authentik-version", constants.VERSION)
		w.Header().Set("Vary", "X-authentik-version, Etag")
		etagHandler.ServeHTTP(w, r)
	})
}
