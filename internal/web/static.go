package web

import (
	"fmt"
	"net/http"

	"github.com/gorilla/mux"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	staticWeb "goauthentik.io/web"
	staticDocs "goauthentik.io/website"
)

func (ws *WebServer) configureStatic() {
	statRouter := ws.lh.NewRoute().Subrouter()
	indexLessRouter := statRouter.NewRoute().Subrouter()
	indexLessRouter.Use(disableIndex)
	// Media files, always local
	fs := http.FileServer(http.Dir(config.G.Paths.Media))
	var distHandler http.Handler
	var distFs http.Handler
	var authentikHandler http.Handler
	var helpHandler http.Handler
	if config.G.Debug || config.G.Web.LoadLocalFiles {
		ws.log.Debug("Using local static files")
		distFs = http.FileServer(http.Dir("./web/dist"))
		distHandler = http.StripPrefix("/static/dist/", distFs)
		authentikHandler = http.StripPrefix("/static/authentik/", http.FileServer(http.Dir("./web/authentik")))
		helpHandler = http.FileServer(http.Dir("./website/help/"))
	} else {
		statRouter.Use(ws.staticHeaderMiddleware)
		ws.log.Debug("Using packaged static files with aggressive caching")
		distFs = http.FileServer(http.FS(staticWeb.StaticDist))
		distHandler = http.StripPrefix("/static", distFs)
		authentikHandler = http.StripPrefix("/static", http.FileServer(http.FS(staticWeb.StaticAuthentik)))
		helpHandler = http.FileServer(http.FS(staticDocs.Help))
	}
	indexLessRouter.PathPrefix("/static/dist/").Handler(distHandler)
	indexLessRouter.PathPrefix("/static/authentik/").Handler(authentikHandler)

	// Prevent font-loading issues on safari, which loads fonts relatively to the URL the browser is on
	indexLessRouter.PathPrefix("/if/flow/{flow_slug}/assets").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		disableIndex(http.StripPrefix(fmt.Sprintf("/if/flow/%s", vars["flow_slug"]), distFs)).ServeHTTP(rw, r)
	})
	indexLessRouter.PathPrefix("/if/admin/assets").Handler(http.StripPrefix("/if/admin", distFs))
	indexLessRouter.PathPrefix("/if/user/assets").Handler(http.StripPrefix("/if/user", distFs))

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
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "\"public, no-transform\"")
		w.Header().Set("X-authentik-version", constants.VERSION)
		w.Header().Set("Vary", "X-authentik-version")
		h.ServeHTTP(w, r)
	})
}
