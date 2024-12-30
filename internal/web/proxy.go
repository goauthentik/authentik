package web

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httputil"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"
)

var (
	ErrAuthentikStarting = errors.New("authentik starting")
)

func (ws *WebServer) configureProxy() {
	// Reverse proxy to the application server
	director := func(req *http.Request) {
		req.URL.Scheme = ws.upstreamURL.Scheme
		req.URL.Host = ws.upstreamURL.Host
		if _, ok := req.Header["User-Agent"]; !ok {
			// explicitly disable User-Agent so it's not set to default value
			req.Header.Set("User-Agent", "")
		}
		if req.TLS != nil {
			req.Header.Set("X-Forwarded-Proto", "https")
		}
		ws.log.Debug("tracing request to backend", config.Trace(), zap.String("url", req.URL.String()), zap.Any("headers", req.Header))
	}
	rp := &httputil.ReverseProxy{
		Director:  director,
		Transport: ws.upstreamHttpClient().Transport,
	}
	rp.ErrorHandler = ws.proxyErrorHandler
	rp.ModifyResponse = ws.proxyModifyResponse
	ws.mainRouter.PathPrefix(config.Get().Web.Path).Path("/-/health/live/").HandlerFunc(sentry.SentryNoSample(func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(200)
	}))
	ws.mainRouter.PathPrefix(config.Get().Web.Path).HandlerFunc(sentry.SentryNoSample(func(rw http.ResponseWriter, r *http.Request) {
		if !ws.g.IsRunning() {
			ws.proxyErrorHandler(rw, r, ErrAuthentikStarting)
			return
		}
		before := time.Now()
		if ws.ProxyServer != nil && ws.ProxyServer.HandleHost(rw, r) {
			elapsed := time.Since(before)
			Requests.With(prometheus.Labels{
				"dest": "embedded_outpost",
			}).Observe(float64(elapsed) / float64(time.Second))
			return
		}
		elapsed := time.Since(before)
		Requests.With(prometheus.Labels{
			"dest": "core",
		}).Observe(float64(elapsed) / float64(time.Second))
		r.Body = http.MaxBytesReader(rw, r.Body, 32*1024*1024)
		rp.ServeHTTP(rw, r)
	}))
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	if !errors.Is(err, ErrAuthentikStarting) {
		ws.log.Warn("failed to proxy to backend", zap.Error(err))
	}
	rw.WriteHeader(http.StatusBadGateway)
	em := fmt.Sprintf("failed to connect to authentik backend: %v", err)
	// return json if the client asks for json
	if req.Header.Get("Accept") == "application/json" {
		err = json.NewEncoder(rw).Encode(map[string]string{
			"error": em,
		})
	} else {
		_, err = rw.Write([]byte(em))
	}
	if err != nil {
		ws.log.Warn("failed to write error message", zap.Error(err))
	}
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("X-Powered-By", "authentik")
	r.Header.Del("Server")
	return nil
}
