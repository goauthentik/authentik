package web

import (
	"net/http"
	"net/url"

	log "github.com/sirupsen/logrus"
)

type hostInterceptor struct {
	inner  http.RoundTripper
	host   string
	scheme string
}

func (t hostInterceptor) RoundTrip(r *http.Request) (*http.Response, error) {
	if r.Host != t.host {
		r.Host = t.host
		r.Header.Set("X-Forwarded-Proto", t.scheme)
	}
	return t.inner.RoundTrip(r)
}

func NewHostInterceptor(inner *http.Client, host string) *http.Client {
	aku, err := url.Parse(host)
	if err != nil {
		log.WithField("host", host).WithError(err).Warn("failed to parse host")
	}
	return &http.Client{
		Transport: hostInterceptor{
			inner:  inner.Transport,
			host:   aku.Host,
			scheme: aku.Scheme,
		},
	}
}
