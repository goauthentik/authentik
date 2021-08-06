package ak

import (
	"net/http"

	"github.com/getsentry/sentry-go"
)

type tracingTransport struct {
	inner http.RoundTripper
}

func NewTracingTransport(inner http.RoundTripper) *tracingTransport {
	return &tracingTransport{inner}
}

func (tt *tracingTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	span := sentry.StartSpan(r.Context(), "authentik.go.http_request")
	span.SetTag("url", r.URL.String())
	span.SetTag("method", r.Method)
	defer span.Finish()
	return tt.inner.RoundTrip(r.WithContext(span.Context()))
}
