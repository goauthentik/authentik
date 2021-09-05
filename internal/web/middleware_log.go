package web

import (
	"net/http"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/utils/web"
)

func loggingMiddleware(l *log.Entry) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			span := sentry.StartSpan(r.Context(), "authentik.go.request")
			before := time.Now()
			// Call the next handler, which can be another middleware in the chain, or the final handler.
			next.ServeHTTP(w, r)
			after := time.Now()
			l.WithFields(log.Fields{
				"remote": r.RemoteAddr,
				"method": r.Method,
				"took":   after.Sub(before),
				"host":   web.GetHost(r),
			}).Info(r.RequestURI)
			span.Finish()
		})
	}
}
