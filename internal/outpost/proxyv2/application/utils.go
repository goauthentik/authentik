package application

import (
	"net/http"
	"net/url"
	"strconv"
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
	state := a.stateFromRequest(rw, r)
	if state == nil {
		rw.WriteHeader(http.StatusBadRequest)
		return
	}
	if state.Redirect == "" {
		state.Redirect = fallbackRedirect
	}
	a.log.WithField("redirect", state.Redirect).Trace("final redirect")
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
