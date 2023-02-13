package web

import (
	"net/http"
	"net/url"

	log "github.com/sirupsen/logrus"
)

type hostInterceptor struct {
	inner http.RoundTripper
	host  string
}

func (t hostInterceptor) RoundTrip(r *http.Request) (*http.Response, error) {
	r.Host = t.host
	return t.inner.RoundTrip(r)
}

func NewHostInterceptor(inner *http.Client, host string) *http.Client {
	aku, err := url.Parse(host)
	if err != nil {
		log.WithField("host", host).WithError(err).Warn("failed to parse host")
	}
	return &http.Client{
		Transport: hostInterceptor{
			inner: inner.Transport,
			host:  aku.Host,
		},
	}
}
