package web

import (
	"net/http"
)

var xForwardedHost = http.CanonicalHeaderKey("X-Forwarded-Host")

func GetHost(req *http.Request) string {
	host := req.Host
	if req.Header.Get(xForwardedHost) != "" {
		host = req.Header.Get(xForwardedHost)
	}
	return host
}
