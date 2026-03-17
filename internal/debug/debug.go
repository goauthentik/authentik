package debug

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/pprof"
	"os"
	"runtime"

	"github.com/gorilla/mux"
	"github.com/grafana/pyroscope-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/web"
)

var l = log.WithField("logger", "authentik.debugger.go")

func EnableDebugServer(appName string) {
	if !config.Get().Debug {
		return
	}
	h := mux.NewRouter()
	enablePyroscope(appName)
	h.HandleFunc("/debug/pprof/", pprof.Index)
	h.HandleFunc("/debug/pprof/cmdline", pprof.Cmdline)
	h.HandleFunc("/debug/pprof/profile", pprof.Profile)
	h.HandleFunc("/debug/pprof/symbol", pprof.Symbol)
	h.HandleFunc("/debug/pprof/trace", pprof.Trace)
	h.HandleFunc("/debug/dump_config", func(w http.ResponseWriter, r *http.Request) {
		enc := json.NewEncoder(w)
		enc.SetEscapeHTML(true)
		enc.SetIndent("", "\t")
		_ = enc.Encode(config.Get())
	})
	h.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		_ = h.Walk(func(route *mux.Route, router *mux.Router, ancestors []*mux.Route) error {
			tpl, err := route.GetPathTemplate()
			if err != nil {
				return nil
			}
			_, err = fmt.Fprintf(w, "<a href='%[1]s'>%[1]s</a><br>", tpl)
			if err != nil {
				l.WithError(err).Warning("failed to write index")
				return nil
			}
			return nil
		})
	})
	go func() {
		l.WithField("listen", config.Get().Listen.Debug).Info("Starting Debug server")
		err := http.ListenAndServe(
			config.Get().Listen.Debug,
			web.NewLoggingHandler(l, nil)(h),
		)
		if l != nil {
			l.WithError(err).Warn("failed to start debug server")
		}
	}()
}

func enablePyroscope(appName string) {
	p, pok := os.LookupEnv("AUTHENTIK_PYROSCOPE_HOST")
	if !pok {
		return
	}
	l.Debug("Enabling pyroscope")
	runtime.SetMutexProfileFraction(5)
	runtime.SetBlockProfileRate(5)
	hostname, err := os.Hostname()
	if err != nil {
		panic(err)
	}
	_, err = pyroscope.Start(pyroscope.Config{
		ApplicationName: appName,
		ServerAddress:   p,
		Logger:          pyroscope.StandardLogger,
		Tags:            map[string]string{"hostname": hostname},
		ProfileTypes: []pyroscope.ProfileType{
			pyroscope.ProfileCPU,
			pyroscope.ProfileAllocObjects,
			pyroscope.ProfileAllocSpace,
			pyroscope.ProfileInuseObjects,
			pyroscope.ProfileInuseSpace,
			pyroscope.ProfileGoroutines,
			pyroscope.ProfileMutexCount,
			pyroscope.ProfileMutexDuration,
			pyroscope.ProfileBlockCount,
			pyroscope.ProfileBlockDuration,
		},
	})
	if err != nil {
		panic(err)
	}
}
