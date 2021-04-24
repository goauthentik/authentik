package proxy

import "net/http"

var xForwardedHost = http.CanonicalHeaderKey("X-Forwarded-Host")

func getHost(req *http.Request) string {
	if req.Header.Get(xForwardedHost) != "" {
		return req.Header.Get(xForwardedHost)
	}
	return req.Host
}
