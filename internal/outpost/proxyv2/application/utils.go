package application

import (
	"fmt"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

func urlJoin(originalUrl string, newPath string) string {
	u, err := url.JoinPath(originalUrl, newPath)
	if err != nil {
		return originalUrl
	}
	return u
}

func (a *Application) redirect(rw http.ResponseWriter, r *http.Request) {
	fallbackRedirect := a.proxyConfig.ExternalHost
	state := a.stateFromRequest(r)
	if state == nil {
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	if state.Redirect == "" {
		state.Redirect = fallbackRedirect
	}
	a.log.WithField("redirect", state.Redirect).Trace("final redirect")
	a.addCORSHeaders(rw, r)
	http.Redirect(rw, r, state.Redirect, http.StatusFound)
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

func contains(s []string, e string) bool {
	for _, a := range s {
		if a == e {
			return true
		}
	}
	return false
}

func cleanseHeaders(headers http.Header) map[string]string {
	h := make(map[string]string)
	for hk, hv := range headers {
		if len(hv) > 0 {
			h[hk] = hv[0]
		}
	}
	return h
}

// setUrlPort sets the port of a URL if it is missing, based on the scheme. This is
// useful for URL comparisons, specifically when comparing against the Origin header.
// If the port is already set, or the scheme is unknown, no changes are made.
// If the scheme is unknown, an error is returned.
func setUrlPort(u *url.URL) error {
	if u.Port() != "" {
		return nil
	}

	// This is designed to support the schemes listed here specifically: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin#description
	switch strings.ToLower(u.Scheme) {
	case "http":
		u.Host = net.JoinHostPort(u.Host, "80")
	case "https":
		u.Host = net.JoinHostPort(u.Host, "443")
	case "ftp":
		u.Host = net.JoinHostPort(u.Host, "21")
	case "ws":
		u.Host = net.JoinHostPort(u.Host, "80")
	case "wss":
		u.Host = net.JoinHostPort(u.Host, "443")
	case "gopher":
		u.Host = net.JoinHostPort(u.Host, "70")
	default:
		return &url.Error{Op: "setUrlPort", URL: u.String(), Err: fmt.Errorf("unknown scheme: %s", u.Scheme)}
	}

	return nil
}
