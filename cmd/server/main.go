package main

import (
	"sync"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/web"
)

func main() {
	log.SetLevel(log.DebugLevel)
	config.DefaultConfig()
	config.LoadConfig("./authentik/lib/default.yml")
	config.LoadConfig("./local.env.yml")
	config.ConfigureLogger()

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
