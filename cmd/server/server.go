package main

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"syscall"
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
	"goauthentik.io/internal/web/tenant_tls"
)

var running = true

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

		u, _ := url.Parse("http://localhost:8000")

		g := gounicorn.New()
		defer func() {
			l.Info("shutting down gunicorn")
			g.Kill()
		}()

		c := make(chan os.Signal, 1)
		signal.Notify(c, syscall.SIGHUP, syscall.SIGUSR2)
		go func() {
			sig := <-c
			if sig == syscall.SIGHUP {
				log.Info("SIGHUP received, forwarding to gunicorn")
				g.Reload()
			}
			if sig == syscall.SIGUSR2 {
				log.Info("SIGUSR2 received, restarting gunicorn")
				g.Restart()
			}
		}()

		ws := web.NewWebServer(g)
		g.HealthyCallback = func() {
			if !config.Get().Outposts.DisableEmbeddedOutpost {
				go attemptProxyStart(ws, u)
			}
		}
		go web.RunMetricsServer()
		go attemptStartBackend(g)

		w, err := config.WatchChanges(func() {
			g.Restart()
		})
		if err != nil {
			l.WithError(err).Warning("failed to start watching for configuration changes, no automatic update will be done")
		}
		if w != nil {
			defer w.Close()
		}

		ws.Start()
		<-ex
		running = false
		l.Info("shutting down webserver")
		go ws.Shutdown()

	},
}

func attemptStartBackend(g *gounicorn.GoUnicorn) {
	for {
		if !running {
			return
		}
		g.Kill()
		log.WithField("logger", "authentik.router").Info("starting gunicorn")
		err := g.Start()
		if err != nil {
			log.WithField("logger", "authentik.router").WithError(err).Error("gunicorn failed to start, restarting")
			continue
		}
		failedChecks := 0
		for range time.Tick(30 * time.Second) {
			if !g.IsRunning() {
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
		// so we just re-use the same one as the outpost uses
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
