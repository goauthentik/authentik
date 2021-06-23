package main

import (
	"errors"
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

	for {
		g := gounicorn.NewGoUnicorn()
		go attemptStartBackend(g)

		ws := web.NewWebServer()
		ws.Run()

		proxy :=

			<-ex
		ws.Stop()
		g.Kill()
	}
	go func() {

		maxTries := 100
		attempt := 0
		for {
			err := attemptProxyStart(u, ex)
			if err != nil {
				attempt += 1
				time.Sleep(5 * time.Second)
				if attempt > maxTries {
					break
				}
			}
		}
	}()
}

func attemptStartBackend(g *gounicorn.GoUnicorn) error {
	for {
		err := g.Start()
		log.WithField("logger", "authentik.g").WithError(err).Warning("gunicorn process died, restarting")
	}
}

func attemptProxyStart(u *url.URL, exitSignal chan os.Signal) (*ak.APIController, error) {
	ac := ak.NewAPIController(*u, config.G.SecretKey)
	if ac == nil {
		return nil, errors.New("failed to start")
	}
	ac.Server = proxy.NewServer(ac)
	return ac, nil
}
