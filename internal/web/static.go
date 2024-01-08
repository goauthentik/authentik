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
	statRouter := ws.lh.NewRoute().Subrouter()
	statRouter.Use(ws.staticHeaderMiddleware)
	indexLessRouter := statRouter.NewRoute().Subrouter()
	indexLessRouter.Use(web.DisableIndex)
	// Media files, always local
	fs := http.FileServer(http.Dir(config.Get().Paths.Media))
	distFs := http.FileServer(http.Dir("./web/dist"))
	distHandler := http.StripPrefix("/static/dist/", distFs)
	authentikHandler := http.StripPrefix("/static/authentik/", http.FileServer(http.Dir("./web/authentik")))
	helpHandler := http.FileServer(http.Dir("./website/help/"))
	indexLessRouter.PathPrefix("/static/dist/").Handler(distHandler)
	indexLessRouter.PathPrefix("/static/authentik/").Handler(authentikHandler)

	// Prevent font-loading issues on safari, which loads fonts relatively to the URL the browser is on
	indexLessRouter.PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		web.DisableIndex(http.StripPrefix(fmt.Sprintf("/if/flow/%s", vars["flow_slug"]), distFs)).ServeHTTP(rw, r)
	})
	indexLessRouter.PathPrefix("/if/admin/assets").Handler(http.StripPrefix("/if/admin", distFs))
	indexLessRouter.PathPrefix("/if/user/assets").Handler(http.StripPrefix("/if/user", distFs))
	indexLessRouter.PathPrefix("/if/rac/{app_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		web.DisableIndex(http.StripPrefix(fmt.Sprintf("/if/rac/%s", vars["app_slug"]), distFs)).ServeHTTP(rw, r)
	})

	indexLessRouter.PathPrefix("/media/").Handler(http.StripPrefix("/media", fs))

	statRouter.PathPrefix("/if/help/").Handler(http.StripPrefix("/if/help/", helpHandler))
	statRouter.PathPrefix("/help").Handler(http.RedirectHandler("/if/help/", http.StatusMovedPermanently))

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
