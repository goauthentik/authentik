package web

import (
	"context"
	"errors"
	"net"
	"net/http"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/proxyv2"
)

type WebServer struct {
	Bind    string
	BindTLS bool

	LegacyProxy bool

	stop chan struct{} // channel for waiting shutdown

	ProxyServer *proxyv2.ProxyServer

	m   *mux.Router
	lh  *mux.Router
	log *log.Entry
	p   *gounicorn.GoUnicorn
}

func NewWebServer(g *gounicorn.GoUnicorn) *WebServer {
	l := log.WithField("logger", "authentik.router")
	mainHandler := mux.NewRouter()
	if config.G.ErrorReporting.Enabled {
		mainHandler.Use(recoveryMiddleware())
	}
	mainHandler.Use(handlers.ProxyHeaders)
	mainHandler.Use(handlers.CompressHandler)
	logginRouter := mainHandler.NewRoute().Subrouter()
	logginRouter.Use(loggingMiddleware(l))

	ws := &WebServer{
		LegacyProxy: true,

		m:   mainHandler,
		lh:  logginRouter,
		log: l,
		p:   g,
	}
	ws.configureStatic()
	ws.configureRoutes()
	ws.configureProxy()
	return ws
}

func (ws *WebServer) configureRoutes() {
	ws.m.Path("/api/v3/sentry/").HandlerFunc(ws.APISentryProxy)
}

func (ws *WebServer) Start() {
	go ws.listenPlain()
	go ws.listenTLS()
}

func (ws *WebServer) Shutdown() {
	ws.stop <- struct{}{}
}

func (ws *WebServer) listenPlain() {
	ln, err := net.Listen("tcp", config.G.Web.Listen)
	if err != nil {
		ws.log.WithError(err).Fatalf("failed to listen")
	}
	ws.log.WithField("addr", config.G.Web.Listen).Info("Listening")

	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	ws.serve(proxyListener)

	err = http.ListenAndServe(config.G.Web.Listen, ws.m)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ws.log.Errorf("ERROR: http.Serve() - %s", err)
	}
}

func (ws *WebServer) serve(listener net.Listener) {
	srv := &http.Server{
		Handler: ws.m,
	}

	// See https://golang.org/pkg/net/http/#Server.Shutdown
	idleConnsClosed := make(chan struct{})
	go func() {
		<-ws.stop // wait notification for stopping server

		// We received an interrupt signal, shut down.
		if err := srv.Shutdown(context.Background()); err != nil {
			// Error from closing listeners, or context timeout:
			ws.log.Printf("HTTP server Shutdown: %v", err)
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ws.log.Errorf("ERROR: http.Serve() - %s", err)
	}
	<-idleConnsClosed
}
