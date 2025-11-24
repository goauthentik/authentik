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
	staticRouter.Use(web.DisableIndex)

	distFs := http.FileServer(http.Dir("./web/dist"))

	pathStripper := func(handler http.Handler, paths ...string) http.Handler {
		h := handler
		for _, path := range paths {
			h = http.StripPrefix(path, h)
		}
		return h
	}

	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/dist/").Handler(pathStripper(
		distFs,
		"static/dist/",
		config.Get().Web.Path,
	))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/static/authentik/").Handler(pathStripper(
		http.FileServer(http.Dir("./web/authentik")),
		"static/authentik/",
		config.Get().Web.Path,
	))

	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/flow/"+vars["flow_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/admin/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/admin", config.Get().Web.Path), distFs))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/user/assets").Handler(http.StripPrefix(fmt.Sprintf("%sif/user", config.Get().Web.Path), distFs))
	staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/if/rac/{app_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pathStripper(
			distFs,
			"if/rac/"+vars["app_slug"],
			config.Get().Web.Path,
		).ServeHTTP(rw, r)
	})

	// Files, if backend is file
	defaultBackend := config.Get().Storage.Backend
	if defaultBackend == "" {
		defaultBackend = "file"
	}
	mediaBackend := config.Get().Storage.Media.Backend
	if mediaBackend == "" {
		mediaBackend = defaultBackend
	}
	reportsBackend := config.Get().Storage.Reports.Backend
	if reportsBackend == "" {
		reportsBackend = defaultBackend
	}

	defaultStoragePath := config.Get().Storage.File.Path
	if defaultStoragePath == "" {
		defaultStoragePath = "./data"
	}

	if mediaBackend == "file" {
		mediaPath := config.Get().Storage.Media.File.Path
		if mediaPath == "" {
			mediaPath = defaultStoragePath
		}
		mediaPath = mediaPath + "/media"
		fsMedia := http.FileServer(http.Dir(mediaPath))
		staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/media/").Handler(pathStripper(
			http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
				fsMedia.ServeHTTP(w, r)
			}),
			"files/media/",
			config.Get().Web.Path,
		))
	}

	if reportsBackend == "file" {
		reportsPath := config.Get().Storage.Reports.File.Path
		if reportsPath == "" {
			reportsPath = defaultStoragePath
		}
		reportsPath = reportsPath + "/reports"
		fsReports := http.FileServer(http.Dir(reportsPath))
		staticRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/reports/").Handler(pathStripper(
			http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				token := r.URL.Query().Get("token")
				if token == "" {
					http.Error(w, "404 page not found", http.StatusNotFound)
					return
				}
				w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
				fsReports.ServeHTTP(w, r)
			}),
			"files/reports/",
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
		w.Header().Set("X-authentik-version", constants.VERSION())
		w.Header().Set("Vary", "X-authentik-version, Etag")
		etagHandler.ServeHTTP(w, r)
	})
}
