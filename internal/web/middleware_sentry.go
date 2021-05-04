package web

import (
	"encoding/json"
	"net/http"

	sentryhttp "github.com/getsentry/sentry-go/http"
)

func recoveryMiddleware() func(next http.Handler) http.Handler {
	sentryHandler := sentryhttp.New(sentryhttp.Options{})
	return func(next http.Handler) http.Handler {
		sentryHandler.Handle(next)
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			next.ServeHTTP(w, r)
			defer func() {
				re := recover()
				if re == nil {
					return
				}
				err := re.(error)
				if err != nil {
					jsonBody, _ := json.Marshal(struct {
						Successful bool
						Error      string
					}{
						Successful: false,
						Error:      err.Error(),
					})

					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusInternalServerError)
					w.Write(jsonBody)
				}
			}()
		})
	}
}
