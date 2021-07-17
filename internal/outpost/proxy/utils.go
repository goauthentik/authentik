package proxy

import (
	"net"
	"net/http"
	"strconv"
)

var xForwardedHost = http.CanonicalHeaderKey("X-Forwarded-Host")

func getHost(req *http.Request) string {
	host := req.Host
	if req.Header.Get(xForwardedHost) != "" {
		host = req.Header.Get(xForwardedHost)
	}
	hostOnly, _, err := net.SplitHostPort(host)
	if err != nil {
		return host
	}
	return hostOnly
}

// toString Generic to string function, currently supports actual strings and integers
func toString(in interface{}) string {
	switch v := in.(type) {
	case string:
		return v
	case *string:
		return *v
	case int:
		return strconv.Itoa(v)
	}
	return ""
}
