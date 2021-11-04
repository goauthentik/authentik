package main

import (
	"fmt"
	"net/url"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2"
	"goauthentik.io/internal/web"
)

var running = true

func main() {
	log.SetLevel(log.DebugLevel)
	log.SetFormatter(&log.JSONFormatter{})
	config.DefaultConfig()
	err := config.LoadConfig("./authentik/lib/default.yml")
	if err != nil {
		log.WithError(err).Warning("failed to load default config")
	}
	err = config.LoadConfig("./local.env.yml")
	if err != nil {
		log.WithError(err).Debug("no local config to load")
	}
	err = config.FromEnv()
	if err != nil {
		log.WithError(err).Debug("failed to environment variables")
	}
	config.ConfigureLogger()

	if config.G.ErrorReporting.Enabled {
		err := sentry.Init(sentry.ClientOptions{
			Dsn:              config.G.ErrorReporting.DSN,
			AttachStacktrace: true,
			TracesSampleRate: 0.6,
			Release:          fmt.Sprintf("authentik@%s", constants.VERSION),
			Environment:      config.G.ErrorReporting.Environment,
		})
		if err != nil {
			log.WithError(err).Warning("failed to init sentry")
		}
	}

	ex := common.Init()
	defer common.Defer()

	u, _ := url.Parse("http://localhost:8000")

	g := gounicorn.NewGoUnicorn()
	ws := web.NewWebServer(g)
	defer g.Kill()
	defer ws.Shutdown()
	go web.RunMetricsServer()
	for {
		go attemptStartBackend(g)
		ws.Start()
		if !config.G.Web.DisableEmbeddedOutpost {
			go attemptProxyStart(ws, u)
		}

		<-ex
		running = false
		log.WithField("logger", "authentik").Info("shutting down webserver")
		go ws.Shutdown()
		log.WithField("logger", "authentik").Info("killing gunicorn")
		g.Kill()
	}
}

func attemptStartBackend(g *gounicorn.GoUnicorn) {
	for {
		err := g.Start()
		if !running {
			return
		}
		log.WithField("logger", "authentik.router").WithError(err).Warning("gunicorn process died, restarting")
	}
}

func attemptProxyStart(ws *web.WebServer, u *url.URL) {
	maxTries := 100
	attempt := 0
	// Sleep to wait for the app server to start
	time.Sleep(30 * time.Second)
	for {
		log.WithField("logger", "authentik").Debug("attempting to init outpost")
		ac := ak.NewAPIController(*u, config.G.SecretKey)
		if ac == nil {
			attempt += 1
			time.Sleep(1 * time.Second)
			if attempt > maxTries {
				break
			}
			continue
		}
		srv := proxyv2.NewProxyServer(ac, 0)
		ws.ProxyServer = srv
		ac.Server = srv
		log.WithField("logger", "authentik").Debug("attempting to start outpost")
		err := ac.StartBackgorundTasks()
		if err != nil {
			log.WithField("logger", "authentik").WithError(err).Warning("outpost failed to start")
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
