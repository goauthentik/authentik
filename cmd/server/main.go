package main

import (
	"fmt"
	"net/url"
	"os"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxy"
	"goauthentik.io/internal/web"
)

func main() {
	log.SetLevel(log.DebugLevel)
	config.DefaultConfig()
	config.LoadConfig("./authentik/lib/default.yml")
	config.LoadConfig("./local.env.yml")
	config.ConfigureLogger()

	if config.G.ErrorReporting.Enabled {
		sentry.Init(sentry.ClientOptions{
			Dsn:              "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
			AttachStacktrace: true,
			TracesSampleRate: 0.6,
			Release:          fmt.Sprintf("authentik@%s", constants.VERSION),
			Environment:      config.G.ErrorReporting.Environment,
		})
	}

	ex := common.Init()
	defer common.Defer()

	u, _ := url.Parse("http://localhost:8000")

	g := gounicorn.NewGoUnicorn()
	ws := web.NewWebServer()
	defer g.Kill()
	defer ws.Shutdown()
	for {
		go attemptStartBackend(g, ex)
		ws.Start()
		// go attemptProxyStart(u, ex)

		<-ex
		log.WithField("logger", "authentik").Debug("shutting down webserver")
		ws.Shutdown()
		log.WithField("logger", "authentik").Debug("killing gunicorn")
		g.Kill()
	}
}

func attemptStartBackend(g *gounicorn.GoUnicorn, exitSignal chan os.Signal) error {
	for {
		err := g.Start()
		select {
		case <-exitSignal:
			return nil
		default:
			log.WithField("logger", "authentik.g").WithError(err).Warning("gunicorn process died, restarting")
		}
	}
}

func attemptProxyStart(u *url.URL, exitSignal chan os.Signal) error {
	maxTries := 100
	attempt := 0
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
		ac.Server = proxy.NewServer(ac)
		err := ac.Start()
		log.WithField("logger", "authentik").Debug("attempting to start outpost")
		if err != nil {
			attempt += 1
			time.Sleep(5 * time.Second)
			if attempt > maxTries {
				break
			}
			continue
		}
		select {
		case <-exitSignal:
			ac.Shutdown()
			return nil
		default:
			break
		}
	}
	return nil
}
