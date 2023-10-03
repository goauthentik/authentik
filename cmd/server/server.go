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
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2"
	sentryutils "goauthentik.io/internal/utils/sentry"
	webutils "goauthentik.io/internal/utils/web"
	"goauthentik.io/internal/web"
	"goauthentik.io/internal/web/tenant_tls"
)

var rootCmd = &cobra.Command{
	Use:     "authentik",
	Short:   "Start authentik instance",
	Version: constants.FullVersion(),
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		log.SetLevel(log.DebugLevel)
		log.SetFormatter(&log.JSONFormatter{
			FieldMap: log.FieldMap{
				log.FieldKeyMsg:  "event",
				log.FieldKeyTime: "timestamp",
			},
			DisableHTMLEscape: true,
		})
	},
	Run: func(cmd *cobra.Command, args []string) {
		debug.EnableDebugServer()
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

		u, err := url.Parse(fmt.Sprintf("http://%s", config.Get().Listen.HTTP))
		if err != nil {
			panic(err)
		}

		ws := web.NewWebServer()
		ws.Core().HealthyCallback = func() {
			if config.Get().Outposts.DisableEmbeddedOutpost {
				return
			}
			go attemptProxyStart(ws, u)
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
		// Init tenant_tls here too since it requires an API Client,
		// so we just reuse the same one as the outpost uses
		tw := tenant_tls.NewWatcher(ac.Client)
		go tw.Start()
		ws.TenantTLS = tw
		ac.AddRefreshHandler(func() {
			tw.Check()
		})

		srv := proxyv2.NewProxyServer(ac)
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
