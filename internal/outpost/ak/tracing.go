package ak

import (
	"context"
	"net/http"

	"github.com/getsentry/sentry-go"
)

type tracingTransport struct {
	inner http.RoundTripper
	ctx   context.Context
}

func NewTracingTransport(ctx context.Context, inner http.RoundTripper) *tracingTransport {
	return &tracingTransport{inner, ctx}
}

func (tt *tracingTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	span := sentry.StartSpan(tt.ctx, "authentik.go.http_request")
	span.SetTag("url", r.URL.String())
	span.SetTag("method", r.Method)
	defer span.Finish()
	return tt.inner.RoundTrip(r.WithContext(span.Context()))
}
