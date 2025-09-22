package web

import (
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/sentry"
	"goauthentik.io/internal/utils/web"
	staticWeb "goauthentik.io/web"
)

var (
	ErrAuthentikStarting = errors.New("authentik starting")
)

const (
	maxBodyBytes = 32 * 1024 * 1024
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
		if !web.IsRequestFromTrustedProxy(req) {
			// If the request isn't coming from a trusted proxy, delete MTLS headers
			req.Header.Del("SSL-Client-Cert")             // nginx-ingress
			req.Header.Del("X-Forwarded-TLS-Client-Cert") // traefik
			req.Header.Del("X-Forwarded-Client-Cert")     // envoy
		}
		if req.TLS != nil {
			req.Header.Set("X-Forwarded-Proto", "https")
			if len(req.TLS.PeerCertificates) > 0 {
				pems := make([]string, len(req.TLS.PeerCertificates))
				for i, crt := range req.TLS.PeerCertificates {
					pem := pem.EncodeToMemory(&pem.Block{
						Type:  "CERTIFICATE",
						Bytes: crt.Raw,
					})
					pems[i] = "Cert=" + url.QueryEscape(string(pem))
				}
				req.Header.Set("X-Forwarded-Client-Cert", strings.Join(pems, ","))
			}
		}
		ws.log.WithField("url", req.URL.String()).WithField("headers", req.Header).Trace("tracing request to backend")
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
		r.Body = http.MaxBytesReader(rw, r.Body, maxBodyBytes)
		rp.ServeHTTP(rw, r)
	}))
}

func (ws *WebServer) proxyErrorHandler(rw http.ResponseWriter, req *http.Request, err error) {
	accept := req.Header.Get("Accept")

	header := rw.Header()

	if errors.Is(err, ErrAuthentikStarting) {
		header.Set("Retry-After", "5")

		if strings.Contains(accept, "application/json") {
			header.Set("Content-Type", "application/json")

			err = json.NewEncoder(rw).Encode(map[string]string{
				"error": "authentik starting",
			})

			if err != nil {
				ws.log.WithError(err).Warning("failed to write error message")
				return
			}
		} else if strings.Contains(accept, "text/html") {
			header.Set("Content-Type", "text/html")
			rw.WriteHeader(http.StatusServiceUnavailable)

			loadingSplashFile, err := staticWeb.StaticDir.Open("standalone/loading/startup.html")

			if err != nil {
				ws.log.WithError(err).Warning("failed to open startup splash screen")
				return
			}

			loadingSplashHTML, err := io.ReadAll(loadingSplashFile)

			if err != nil {
				ws.log.WithError(err).Warning("failed to read startup splash screen")
				return
			}

			_, err = rw.Write(loadingSplashHTML)

			if err != nil {
				ws.log.WithError(err).Warning("failed to write startup splash screen")
				return
			}
		} else {
			header.Set("Content-Type", "text/plain")
			rw.WriteHeader(http.StatusServiceUnavailable)

			// Fallback to just a status message
			_, err = rw.Write([]byte("authentik starting"))

			if err != nil {
				ws.log.WithError(err).Warning("failed to write initializing HTML")
			}
		}

		return
	}

	ws.log.WithError(err).Warning("failed to proxy to backend")

	em := fmt.Sprintf("failed to connect to authentik backend: %v", err)

	if strings.Contains(accept, "application/json") {
		header.Set("Content-Type", "application/json")
		rw.WriteHeader(http.StatusBadGateway)

		err = json.NewEncoder(rw).Encode(map[string]string{
			"error": em,
		})
	} else {
		header.Set("Content-Type", "text/plain")
		rw.WriteHeader(http.StatusBadGateway)

		_, err = rw.Write([]byte(em))
	}

	if err != nil {
		ws.log.WithError(err).Warning("failed to write error message")
	}
}

func (ws *WebServer) proxyModifyResponse(r *http.Response) error {
	r.Header.Set("X-Powered-By", "authentik")
	r.Header.Del("Server")
	return nil
}
