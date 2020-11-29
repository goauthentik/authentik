package server

import "net/http"

func SetUserAgent(inner http.RoundTripper, userAgent string) http.RoundTripper {
	return &addUGA{
		inner: inner,
		Agent: userAgent,
	}
}

type addUGA struct {
	inner http.RoundTripper
	Agent string
}

func (ug *addUGA) RoundTrip(r *http.Request) (*http.Response, error) {
	r.Header.Set("User-Agent", ug.Agent)
	return ug.inner.RoundTrip(r)
}
