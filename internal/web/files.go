package web

import (
	"net/http"

	"github.com/go-http-utils/etag"
	"github.com/gorilla/mux"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
)

type File struct {
	ID string `gorm:"primaryKey"`

	Name     string
	Content  []byte
	Location string
	Public   bool
}

func (ws *WebServer) configureFiles() {
	// Setup routers
	filesRouter := ws.loggingRouter.NewRoute().Subrouter()
	filesRouter.Use(ws.filesHeaderMiddleware)

	filesRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/public/{pk}").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		pk := vars["pk"]

		var file File
		ws.postgresClient.First(&file, "id = ? AND public = true AND content <> NULL", pk)

		// TODO: get from DB
		rw.Write(file.Content)
	})

	filesRouter.PathPrefix(config.Get().Web.Path).PathPrefix("/files/private/{pk}").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)

		// TODO: check session

		pk := vars["pk"]

		var file File
		ws.postgresClient.First(&file, "id = ? AND content <> NULL", pk)

		rw.Write([]byte(file.Content))
	})
}

// TODO: anything else?
func (ws *WebServer) filesHeaderMiddleware(h http.Handler) http.Handler {
	etagHandler := etag.Handler(h, false)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "public, no-transform")
		w.Header().Set("X-authentik-version", constants.VERSION)
		w.Header().Set("Vary", "X-authentik-version, Etag")
		etagHandler.ServeHTTP(w, r)
	})
}
