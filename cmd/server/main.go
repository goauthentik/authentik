package main

import (
	"fmt"
	"sync"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/gounicorn"
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
		defer sentry.Flush(time.Second * 5)
		defer sentry.Recover()
	}

	rl := log.WithField("logger", "authentik.g")
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		g := gounicorn.NewGoUnicorn()
		for {
			err := g.Start()
			rl.WithError(err).Warning("gunicorn process died, restarting")
		}
	}()
	go func() {
		defer wg.Done()
		ws := web.NewWebServer()
		ws.Run()
	}()
	wg.Wait()
}
