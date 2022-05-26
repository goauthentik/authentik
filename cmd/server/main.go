package main

import (
	"fmt"
	"net/http"
	"net/url"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2"
	"goauthentik.io/internal/web"
	"goauthentik.io/internal/web/tenant_tls"
)

var running = true

func main() {
	log.SetLevel(log.DebugLevel)
	log.SetFormatter(&log.JSONFormatter{
		FieldMap: log.FieldMap{
			log.FieldKeyMsg:  "event",
			log.FieldKeyTime: "timestamp",
		},
		DisableHTMLEscape: true,
	})
	go debug.EnableDebugServer()
	l := log.WithField("logger", "authentik.root")
	config.DefaultConfig()
	err := config.LoadConfig("./authentik/lib/default.yml")
	if err != nil {
		l.WithError(err).Warning("failed to load default config")
	}
	err = config.LoadConfig("./local.env.yml")
	if err != nil {
		l.WithError(err).Debug("no local config to load")
	}
	err = config.FromEnv()
	if err != nil {
		l.WithError(err).Debug("failed to environment variables")
	}
	config.ConfigureLogger()

	if config.G.ErrorReporting.Enabled {
		err := sentry.Init(sentry.ClientOptions{
			Dsn:              config.G.ErrorReporting.DSN,
			AttachStacktrace: true,
			TracesSampleRate: config.G.ErrorReporting.SampleRate,
			Release:          fmt.Sprintf("authentik@%s", constants.VERSION),
			Environment:      config.G.ErrorReporting.Environment,
			IgnoreErrors: []string{
				http.ErrAbortHandler.Error(),
			},
		})
		if err != nil {
			l.WithError(err).Warning("failed to init sentry")
		}
	}

	ex := common.Init()
	defer common.Defer()

	u, _ := url.Parse("http://localhost:8000")

	g := gounicorn.NewGoUnicorn()
	ws := web.NewWebServer(g)
	g.HealthyCallback = func() {
		if !config.G.Web.DisableEmbeddedOutpost {
			go attemptProxyStart(ws, u)
		}
	}
	go web.RunMetricsServer()
	go attemptStartBackend(g)
	ws.Start()
	<-ex
	running = false
	l.Info("shutting down gunicorn")
	go g.Kill()
	l.Info("shutting down webserver")
	go ws.Shutdown()
}

func attemptStartBackend(g *gounicorn.GoUnicorn) {
	for {
		if !running {
			return
		}
		err := g.Start()
		log.WithField("logger", "authentik.router").WithError(err).Warning("gunicorn process died, restarting")
	}
}

func attemptProxyStart(ws *web.WebServer, u *url.URL) {
	maxTries := 100
	attempt := 0
	l := log.WithField("logger", "authentik.server")
	for {
		l.Debug("attempting to init outpost")
		ac := ak.NewAPIController(*u, config.G.SecretKey)
		if ac == nil {
			attempt += 1
			time.Sleep(1 * time.Second)
			if attempt > maxTries {
				break
			}
			continue
		}
		// Init tenant_tls here too since it requires an API Client,
		// so we just re-use the same one as the outpost uses
		tw := tenant_tls.NewWatcher(ac.Client)
		go tw.Start()
		ws.TenantTLS = tw
		ac.AddRefreshHandler(func() {
			tw.Check()
		})

		srv := proxyv2.NewProxyServer(ac, 0)
		ws.ProxyServer = srv
		ac.Server = srv
		l.Debug("attempting to start outpost")
		err := ac.StartBackgroundTasks()
		if err != nil {
			l.WithError(err).Warning("outpost failed to start")
			attempt += 1
			time.Sleep(15 * time.Second)
			if attempt > maxTries {
				break
			}
			continue
		} else {
			select {}
		}
	}
}
