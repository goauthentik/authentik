package web

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"goauthentik.io/internal/config"
)

type SentryRequest struct {
	DSN string `json:"dsn"`
}

func (ws *WebServer) APISentryProxy() http.HandlerFunc {
	fallbackHandler := func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
	}
	if !config.Get().ErrorReporting.Enabled {
		ws.log.Debug("error reporting disabled")
		return fallbackHandler
	}
	dsn, err := url.Parse(config.Get().ErrorReporting.SentryDSN)
	if err != nil {
		ws.log.WithError(err).Warning("invalid sentry DSN")
		return fallbackHandler
	}
	projectId, err := strconv.Atoi(strings.TrimPrefix(dsn.Path, "/"))
	if err != nil {
		ws.log.WithError(err).Warning("failed to get sentry project id")
		return fallbackHandler
	}
	return func(rw http.ResponseWriter, r *http.Request) {
		fb := &bytes.Buffer{}
		_, err := io.Copy(fb, r.Body)
		if err != nil {
			ws.log.Debug("failed to read body")
			rw.WriteHeader(http.StatusBadRequest)
			return
		}
		lines := strings.Split(fb.String(), "\n")
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
		if sd.DSN != config.Get().ErrorReporting.SentryDSN {
			rw.WriteHeader(http.StatusBadRequest)
			return
		}
		res, err := http.DefaultClient.Post(
			fmt.Sprintf(
				"https://%s/api/%d/envelope/",
				dsn.Host,
				projectId,
			),
			"application/x-sentry-envelope",
			fb,
		)
		if err != nil {
			ws.log.WithError(err).Warning("failed to proxy sentry")
			rw.WriteHeader(http.StatusBadRequest)
			return
		}
		rw.WriteHeader(res.StatusCode)
	}
}
