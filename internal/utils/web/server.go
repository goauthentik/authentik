package web

import (
	"net/http"
	"time"

	"goauthentik.io/internal/config"
)

func durationOrFallback(raw string, fallback time.Duration) time.Duration {
	p, err := time.ParseDuration(raw)
	if err != nil {
		return fallback
	}
	return p
}

func Server(h http.Handler) *http.Server {
	c := config.Get()
	return &http.Server{
		Handler:           h,
		ReadHeaderTimeout: durationOrFallback(c.Web.TimeoutHttpReadHeader, 5*time.Second),
		ReadTimeout:       durationOrFallback(c.Web.TimeoutHttpRead, 30*time.Second),
		WriteTimeout:      durationOrFallback(c.Web.TimeoutHttpWrite, 60*time.Second),
		IdleTimeout:       durationOrFallback(c.Web.TimeoutHttpIdle, 120*time.Second),
		MaxHeaderBytes:    http.DefaultMaxHeaderBytes,
	}
}
