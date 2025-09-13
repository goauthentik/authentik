package web

import (
	"net/http"
)

var xForwardedHost = http.CanonicalHeaderKey("X-Forwarded-Host")
var xForwardedPort = http.CanonicalHeaderKey("X-Forwarded-Port")

func GetHost(req *http.Request) string {
	host := req.Host
	xff_host := req.Header.Get(xForwardedHost)
	if xff_host != "" {
		xff_port := req.Header.Get(xForwardedPort)
        if xff_port != "" {
			host = xff_host + ":" + xff_port
		} else {
			host = xff_host
		}
	}
	return host
}
