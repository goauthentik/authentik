package web

import (
	"net/http"
	"sync"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

type WebServer struct {
	Bind    string
	BindTLS bool

	LegacyProxy bool

	m   *mux.Router
	lh  *mux.Router
	log *log.Entry
}

func NewWebServer() *WebServer {
	mainHandler := mux.NewRouter()
	mainHandler.Use(recoveryMiddleware())
	mainHandler.Use(handlers.ProxyHeaders)
	mainHandler.Use(handlers.CompressHandler)
	logginRouter := mainHandler.NewRoute().Subrouter()
	logginRouter.Use(loggingMiddleware)
	ws := &WebServer{
		LegacyProxy: true,

		m:   mainHandler,
		lh:  logginRouter,
		log: log.WithField("logger", "authentik.g.web"),
	}
	ws.configureStatic()
	ws.configureProxy()
	return ws
}

func (ws *WebServer) Run() {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		ws.listenPlain()
	}()
	go func() {
		defer wg.Done()
		// ws.listenTLS()
	}()
	wg.Done()
}

func (ws *WebServer) listenPlain() {
	ws.log.WithField("addr", config.G.Web.Listen).Info("Running")
	http.ListenAndServe(config.G.Web.Listen, ws.m)
}
