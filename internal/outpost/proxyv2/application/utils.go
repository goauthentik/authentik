package application

import (
	"net/http"
	"net/url"
	"slices"
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
	url := a.proxyConfig.ExternalHost
	state := a.stateFromRequest(rw, r)
	if state != nil && state.Redirect != "" {
		url = state.Redirect
	}
	a.log.WithField("redirect", url).Trace("final redirect")
	http.Redirect(rw, r, url, http.StatusFound)
}

// toString Generic to string function, currently supports actual strings and integers
func toString(in any) string {
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
	return slices.Contains(s, e)
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
