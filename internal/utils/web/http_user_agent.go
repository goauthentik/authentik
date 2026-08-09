package web

import (
	"net/http"
)

type userAgentTransport struct {
	inner http.RoundTripper
	ua    string
}

func NewUserAgentTransport(ua string, inner http.RoundTripper) *userAgentTransport {
	return &userAgentTransport{inner, ua}
}

func (uat *userAgentTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	r.Header.Set("User-Agent", uat.ua)
	return uat.inner.RoundTrip(r)
}
