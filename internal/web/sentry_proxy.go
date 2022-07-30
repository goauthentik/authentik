package web

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"strings"

	"goauthentik.io/internal/config"
)

type SentryRequest struct {
	DSN string `json:"dsn"`
}

func (ws *WebServer) APISentryProxy(rw http.ResponseWriter, r *http.Request) {
	if !config.Get().ErrorReporting.Enabled {
		ws.log.Debug("error reporting disabled")
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	fullBody, err := ioutil.ReadAll(r.Body)
	if err != nil {
		ws.log.Debug("failed to read body")
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	lines := strings.Split(string(fullBody), "\n")
	if len(lines) < 1 {
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	sd := SentryRequest{}
	err = json.Unmarshal([]byte(lines[0]), &sd)
	if err != nil {
		ws.log.WithError(err).Warning("failed to parse sentry request")
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	if sd.DSN != config.Get().ErrorReporting.DSN {
		ws.log.WithField("have", sd.DSN).WithField("expected", config.Get().ErrorReporting.DSN).Debug("invalid DSN")
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	res, err := http.DefaultClient.Post("https://sentry.beryju.org/api/8/envelope/", "application/octet-stream", strings.NewReader(string(fullBody)))
	if err != nil {
		ws.log.WithError(err).Warning("failed to proxy sentry")
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	rw.WriteHeader(res.StatusCode)
}
