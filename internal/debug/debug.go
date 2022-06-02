package debug

import (
	"net/http"
	"net/http/pprof"
	"os"
	"strings"

	log "github.com/sirupsen/logrus"
)

func EnableDebugServer() {
	l := log.WithField("logger", "authentik.go_debugger")
	if deb := os.Getenv("AUTHENTIK_DEBUG"); strings.ToLower(deb) != "true" {
		l.Info("not enabling debug server, set `AUTHENTIK_DEBUG` to `true` to enable it.")
		return
	}
	h := http.NewServeMux()
	h.HandleFunc("/debug/pprof/", pprof.Index)
	h.HandleFunc("/debug/pprof/cmdline", pprof.Cmdline)
	h.HandleFunc("/debug/pprof/profile", pprof.Profile)
	h.HandleFunc("/debug/pprof/symbol", pprof.Symbol)
	h.HandleFunc("/debug/pprof/trace", pprof.Trace)
	l.Println(http.ListenAndServe("0.0.0.0:9900", nil))
}
