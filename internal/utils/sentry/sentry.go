package sentry

import (
	"context"
	"net/http"

	"github.com/getsentry/sentry-go"
)

type contextSentryNoSample struct{}

func SentryNoSample(handler func(rw http.ResponseWriter, r *http.Request)) func(http.ResponseWriter, *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), contextSentryNoSample{}, true)
		handler(w, r.WithContext(ctx))
	}
}

func SentryNoSampleMiddleware(h http.Handler) http.Handler {
	return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		ctx := context.WithValue(r.Context(), contextSentryNoSample{}, true)
		h.ServeHTTP(rw, r.WithContext(ctx))
	})
}

func SamplerFunc(defaultRate float64) sentry.TracesSampler {
	return func(ctx sentry.SamplingContext) float64 {
		data, ok := ctx.Span.Context().Value(contextSentryNoSample{}).(bool)
		if data && ok {
			return 0
		}
		return defaultRate
	}
}
