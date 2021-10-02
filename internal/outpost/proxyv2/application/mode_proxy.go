package application

import (
	"context"
	"crypto/tls"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/outpost/proxyv2/templates"
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
	rp := &httputil.ReverseProxy{Director: a.proxyModifyRequest(u)}
	rp.Transport = ak.NewTracingTransport(context.TODO(), a.getUpstreamTransport())
	rp.ErrorHandler = a.newProxyErrorHandler(templates.GetTemplates())
	rp.ModifyResponse = a.proxyModifyResponse
	a.mux.PathPrefix("/").HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		claims, err := a.getClaims(r)
		if claims == nil && a.IsAllowlisted(r) {
			a.log.Trace("path can be accessed without authentication")
		} else if claims == nil && err != nil {
			a.redirectToStart(rw, r)
			return
		} else {
			a.addHeaders(r, claims)
		}
		before := time.Now()
		rp.ServeHTTP(rw, r)
		after := time.Since(before)

		user := ""
		if claims != nil {
			user = claims.Email
		}
		metrics.UpstreamTiming.With(prometheus.Labels{
			"outpost_name":  a.outpostName,
			"upstream_host": u.String(),
			"scheme":        r.URL.Scheme,
			"method":        r.Method,
			"path":          r.URL.Path,
			"host":          web.GetHost(r),
			"user":          user,
		}).Observe(float64(after))
	})
	return nil
}

func (a *Application) proxyModifyRequest(u *url.URL) func(req *http.Request) {
	return func(req *http.Request) {
		req.URL.Scheme = u.Scheme
		req.URL.Host = u.Host
	}
}

func (a *Application) proxyModifyResponse(res *http.Response) error {
	return nil
}
