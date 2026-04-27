package web

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"

	"goauthentik.io/internal/config"
)

// configureTiles registers a reverse proxy at /tiles/* that forwards to the
// configured tile server upstream. When AUTHENTIK_TILES__UPSTREAM is empty
// the route is not registered, so requests fall through to the catch-all
// proxy and the Python backend returns 404.
func (ws *WebServer) configureTiles() {
	upstream := strings.TrimSpace(config.Get().Tiles.Upstream)
	if upstream == "" {
		return
	}

	target, err := url.Parse(upstream)
	if err != nil || target.Scheme == "" || target.Host == "" {
		ws.log.WithError(err).WithField("upstream", upstream).Warning(
			"invalid AUTHENTIK_TILES__UPSTREAM, skipping /tiles/* proxy",
		)
		return
	}

	tilesRouter := ws.loggingRouter.NewRoute().Subrouter()
	prefix := strings.TrimRight(config.Get().Web.Path, "/") + "/tiles/"

	rp := httputil.NewSingleHostReverseProxy(target)
	originalDirector := rp.Director
	rp.Director = func(req *http.Request) {
		originalDirector(req)
		req.URL.Path = "/" + strings.TrimPrefix(strings.TrimPrefix(req.URL.Path, prefix), "/")
		req.URL.RawPath = ""
		req.Host = target.Host
		// Tile requests don't need any user state, and we don't want
		// upstream tile servers to see authentik session material.
		req.Header.Del("Cookie")
		req.Header.Del("Authorization")
	}
	rp.ModifyResponse = func(resp *http.Response) error {
		// Tile bytes are immutable; encourage shared caches to keep them.
		if resp.Header.Get("Cache-Control") == "" {
			resp.Header.Set("Cache-Control", "public, max-age=86400, immutable")
		}
		return nil
	}

	tilesRouter.PathPrefix(prefix).Handler(rp)
	ws.log.WithField("upstream", upstream).WithField("prefix", prefix).Debug(
		"registered tile reverse-proxy",
	)
}
