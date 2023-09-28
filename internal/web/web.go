package web

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"os"
	"path"
	"time"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/proxyv2"
	"goauthentik.io/internal/utils/web"
	"goauthentik.io/internal/web/tenant_tls"
)

type WebServer struct {
	Bind    string
	BindTLS bool

	stop chan struct{} // channel for waiting shutdown

	ProxyServer *proxyv2.ProxyServer
	TenantTLS   *tenant_tls.Watcher

	g   *gounicorn.GoUnicorn
	gr  bool
	m   *mux.Router
	lh  *mux.Router
	log *log.Entry
	uc  *http.Client
	ul  *url.URL
}

const UnixSocketName = "authentik-core.sock"

func NewWebServer() *WebServer {
	l := log.WithField("logger", "authentik.router")
	mainHandler := mux.NewRouter()
	mainHandler.Use(web.ProxyHeaders())
	mainHandler.Use(handlers.CompressHandler)
	loggingHandler := mainHandler.NewRoute().Subrouter()
	loggingHandler.Use(web.NewLoggingHandler(l, nil))

	tmp := os.TempDir()
	socketPath := path.Join(tmp, "authentik-core.sock")

	// create http client to talk to backend, normal client if we're in debug more
	// and a client that connects to our socket when in non debug mode
	var upstreamClient *http.Client
	if config.Get().Debug {
		upstreamClient = http.DefaultClient
	} else {
		upstreamClient = &http.Client{
			Transport: &http.Transport{
				DialContext: func(_ context.Context, _, _ string) (net.Conn, error) {
					return net.Dial("unix", socketPath)
				},
			},
		}
	}

	u, _ := url.Parse("http://localhost:8000")

	ws := &WebServer{
		m:   mainHandler,
		lh:  loggingHandler,
		log: l,
		gr:  true,
		uc:  upstreamClient,
		ul:  u,
	}
	ws.configureStatic()
	ws.configureProxy()
	ws.g = gounicorn.New(func() bool {
		req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("%s/-/health/live/", ws.ul.String()), nil)
		if err != nil {
			ws.log.WithError(err).Warning("failed to create request for healthcheck")
			return false
		}
		req.Header.Set("User-Agent", "goauthentik.io/router/healthcheck")
		res, err := ws.upstreamHttpClient().Do(req)
		if err == nil && res.StatusCode == 204 {
			return true
		}
		return false
	})
	return ws
}

func (ws *WebServer) Start() {
	go ws.runMetricsServer()
	go ws.attemptStartBackend()
	go ws.listenPlain()
	go ws.listenTLS()
}

func (ws *WebServer) attemptStartBackend() {
	for {
		if !ws.gr {
			return
		}
		err := ws.g.Start()
		log.WithField("logger", "authentik.router").WithError(err).Warning("gunicorn process died, restarting")
		if err != nil {
			log.WithField("logger", "authentik.router").WithError(err).Error("gunicorn failed to start, restarting")
			continue
		}
		failedChecks := 0
		for range time.NewTicker(30 * time.Second).C {
			if !ws.g.IsRunning() {
				log.WithField("logger", "authentik.router").Warningf("gunicorn process failed healthcheck %d times", failedChecks)
				failedChecks += 1
			}
			if failedChecks >= 3 {
				log.WithField("logger", "authentik.router").WithError(err).Error("gunicorn process failed healthcheck three times, restarting")
				break
			}
		}
	}
}

func (ws *WebServer) Core() *gounicorn.GoUnicorn {
	return ws.g
}

func (ws *WebServer) upstreamHttpClient() *http.Client {
	return ws.uc
}

func (ws *WebServer) Shutdown() {
	ws.log.Info("shutting down gunicorn")
	ws.g.Kill()
	ws.stop <- struct{}{}
}

func (ws *WebServer) listenPlain() {
	ln, err := net.Listen("tcp", config.Get().Listen.HTTP)
	if err != nil {
		ws.log.WithError(err).Warning("failed to listen")
		return
	}
	proxyListener := &proxyproto.Listener{Listener: ln}
	defer proxyListener.Close()

	ws.log.WithField("listen", config.Get().Listen.HTTP).Info("Starting HTTP server")
	ws.serve(proxyListener)
	ws.log.WithField("listen", config.Get().Listen.HTTP).Info("Stopping HTTP server")
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
			ws.log.WithError(err).Warning("HTTP server Shutdown")
		}
		close(idleConnsClosed)
	}()

	err := srv.Serve(listener)
	if err != nil && !errors.Is(err, http.ErrServerClosed) {
		ws.log.WithError(err).Error("ERROR: http.Serve()")
	}
	<-idleConnsClosed
}
