package main

import (
	"fmt"
	"net/http"
	"net/url"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/gounicorn"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2"
	sentryutils "goauthentik.io/internal/utils/sentry"
	webutils "goauthentik.io/internal/utils/web"
	"goauthentik.io/internal/web"
)

var rootCmd = &cobra.Command{
	Use:              "authentik",
	Short:            "Start authentik instance",
	Version:          constants.FullVersion(),
	PersistentPreRun: common.PreRun,
	Run: func(cmd *cobra.Command, args []string) {
		debug.EnableDebugServer("authentik.core")
		l := log.WithField("logger", "authentik.root")

		if config.Get().ErrorReporting.Enabled {
			err := sentry.Init(sentry.ClientOptions{
				Dsn:              config.Get().ErrorReporting.SentryDSN,
				AttachStacktrace: true,
				EnableTracing:    true,
				TracesSampler:    sentryutils.SamplerFunc(config.Get().ErrorReporting.SampleRate),
				Release:          fmt.Sprintf("authentik@%s", constants.VERSION),
				Environment:      config.Get().ErrorReporting.Environment,
				HTTPTransport:    webutils.NewUserAgentTransport(constants.UserAgent(), http.DefaultTransport),
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

		u, err := url.Parse(fmt.Sprintf("http://%s%s", config.Get().Listen.HTTP, config.Get().Web.Path))
		if err != nil {
			panic(err)
		}

		ws := web.NewWebServer()
		ws.Core().AddHealthyCallback(func() {
			if config.Get().Outposts.DisableEmbeddedOutpost {
				return
			}
			go attemptProxyStart(ws, u)
		})
		if config.Get().Debug {
			w := gounicorn.NewWorker(func() bool {
				return true
			})
			go func() {
				err := w.Start()
				if err != nil {
					l.WithError(err).Warning("failed to start worker")
				}
			}()
		}
		ws.Start()
		<-ex
		l.Info("shutting down webserver")
		go ws.Shutdown()
	},
}

func attemptProxyStart(ws *web.WebServer, u *url.URL) {
	maxTries := 100
	attempt := 0
	l := log.WithField("logger", "authentik.server")
	for {
		l.Debug("attempting to init outpost")
		ac := ak.NewAPIController(*u, config.Get().SecretKey)
		if ac == nil {
			attempt += 1
			time.Sleep(1 * time.Second)
			if attempt > maxTries {
				break
			}
			continue
		}
		ac.AddRefreshHandler(func() {
			ws.BrandTLS.Check()
		})

		srv := proxyv2.NewProxyServer(ac)
		ws.ProxyServer = srv.(*proxyv2.ProxyServer)
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
