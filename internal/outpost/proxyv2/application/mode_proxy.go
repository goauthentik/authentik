package application

import (
	"context"
	"crypto/tls"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/utils/web"
)

func (a *Application) getUpstreamTransport() http.RoundTripper {
	return &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: !*a.proxyConfig.InternalHostSslValidation},
	}
}

func (a *Application) configureProxy() error {
	// Reverse proxy to the application server
	u, err := url.Parse(*a.proxyConfig.InternalHost)
	if err != nil {
		return err
	}
	rsp := sentry.StartSpan(context.TODO(), "authentik.outposts.proxy.application_transport")
	rp := &httputil.ReverseProxy{
		Director:       a.proxyModifyRequest(u),
		Transport:      web.NewTracingTransport(rsp.Context(), a.getUpstreamTransport()),
		ErrorHandler:   a.newProxyErrorHandler(),
		ModifyResponse: a.proxyModifyResponse,
		FlushInterval:  -1,
	}
	a.mux.PathPrefix("/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		defer func() {
			err := recover()
			if err == nil || err == http.ErrAbortHandler {
				return
			}
			a.log.Error("recover in reverse proxy", zap.Error(err.(error)))
		}()
		claims, err := a.checkAuth(rw, r)
		if claims == nil && a.IsAllowlisted(r.URL) {
			a.log.Debug("path can be accessed without authentication", config.Trace())
		} else if claims == nil && err != nil {
			a.log.Debug("no claims", zap.Error(err), config.Trace())
			a.redirectToStart(rw, r)
			return
		} else {
			a.addHeaders(r.Header, claims)
		}
		before := time.Now()
		rp.ServeHTTP(rw, r)
		elapsed := time.Since(before)

		metrics.UpstreamTiming.With(prometheus.Labels{
			"outpost_name":  a.outpostName,
			"upstream_host": r.URL.Host,
			"method":        r.Method,
			"scheme":        r.URL.Scheme,
			"host":          web.GetHost(r),
		}).Observe(float64(elapsed) / float64(time.Second))
	})
	return nil
}

func (a *Application) proxyModifyRequest(ou *url.URL) func(req *http.Request) {
	return func(r *http.Request) {
		r.Header.Set("X-Forwarded-Host", r.Host)
		r.URL.Scheme = ou.Scheme
		r.URL.Host = ou.Host
		claims := a.getClaimsFromSession(r)
		if claims != nil && claims.Proxy != nil && claims.Proxy.BackendOverride != "" {
			u, err := url.Parse(claims.Proxy.BackendOverride)
			if err != nil {
				a.log.Warn("failed parse user backend override", zap.String("backend_override", claims.Proxy.BackendOverride), zap.Error(err))
			} else {
				r.URL.Scheme = u.Scheme
				r.URL.Host = u.Host
			}
		}
		a.log.Debug("final upstream url", zap.String("upstream_url", r.URL.String()))
	}
}

func (a *Application) proxyModifyResponse(res *http.Response) error {
	res.Header.Set("X-Powered-By", "goauthentik.io")
	return nil
}
