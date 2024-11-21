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
	staticRouter := ws.lh.NewRoute().Subrouter()
	staticRouter.Use(ws.staticHeaderMiddleware)
	staticRouter.Use(web.DisableIndex)

	distFs := http.FileServer(http.Dir("./web/dist"))
	authentikHandler := http.StripPrefix("/static/authentik/", http.FileServer(http.Dir("./web/authentik")))

	// Root file paths, from which they should be accessed
	staticRouter.PathPrefix("/static/dist/").Handler(http.StripPrefix("/static/dist/", distFs))
	staticRouter.PathPrefix("/static/authentik/").Handler(authentikHandler)

	// Also serve assets folder in specific interfaces since fonts in patternfly are imported
	// with a relative path
	staticRouter.PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		web.DisableIndex(http.StripPrefix(fmt.Sprintf("/if/flow/%s", vars["flow_slug"]), distFs)).ServeHTTP(rw, r)
	})
	staticRouter.PathPrefix("/if/admin/assets").Handler(http.StripPrefix("/if/admin", distFs))
	staticRouter.PathPrefix("/if/user/assets").Handler(http.StripPrefix("/if/user", distFs))
	staticRouter.PathPrefix("/if/rac/{app_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		web.DisableIndex(http.StripPrefix(fmt.Sprintf("/if/rac/%s", vars["app_slug"]), distFs)).ServeHTTP(rw, r)
	})

	// Media files, if backend is file
	if config.Get().Storage.Media.Backend == "file" {
		fsMedia := http.StripPrefix("/media", http.FileServer(http.Dir(config.Get().Storage.Media.File.Path)))
		staticRouter.PathPrefix("/media/").HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		    w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
		    fsMedia.ServeHTTP(w, r)
		})
	}

	staticRouter.PathPrefix("/if/help/").Handler(http.StripPrefix("/if/help/", http.FileServer(http.Dir("./website/help/"))))
	staticRouter.PathPrefix("/help").Handler(http.RedirectHandler("/if/help/", http.StatusMovedPermanently))

	// Static misc files
	ws.lh.Path("/robots.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header()["Content-Type"] = []string{"text/plain"}
		rw.WriteHeader(200)
		_, err := rw.Write(staticWeb.RobotsTxt)
		if err != nil {
			ws.log.WithError(err).Warning("failed to write response")
		}
	})
	ws.lh.Path("/.well-known/security.txt").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
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
