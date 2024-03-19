package application

import (
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func urlJoin(originalUrl string, newPath string) string {
	u, err := url.JoinPath(originalUrl, newPath)
	if err != nil {
		return originalUrl
	}
	return u
}

func (a *Application) redirectToStart(rw http.ResponseWriter, r *http.Request) {
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.WithError(err).Warning("failed to decode session")
	}
	if r.Header.Get(constants.HeaderAuthorization) != "" && *a.proxyConfig.InterceptHeaderAuth {
		rw.WriteHeader(401)
		er := a.errorTemplates.Execute(rw, ErrorPageData{
			Title:       "Unauthenticated",
			Message:     "Due to 'Receive header authentication' being set, no redirect is performed.",
			ProxyPrefix: "/outpost.goauthentik.io",
		})
		if er != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	}

	redirectUrl := urlJoin(a.proxyConfig.ExternalHost, r.URL.Path)

	if a.Mode() == api.PROXYMODE_FORWARD_DOMAIN {
		dom := strings.TrimPrefix(*a.proxyConfig.CookieDomain, ".")
		// In forward_domain we only check that the current URL's host
		// ends with the cookie domain (remove the leading period if set)
		if !strings.HasSuffix(r.URL.Hostname(), dom) {
			a.log.WithField("url", r.URL.String()).WithField("cd", dom).Warning("Invalid redirect found")
			redirectUrl = a.proxyConfig.ExternalHost
		}
	}
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = redirectUrl
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session before redirect")
		}
	}

	urlArgs := url.Values{
		redirectParam: []string{redirectUrl},
	}
	authUrl := urlJoin(a.proxyConfig.ExternalHost, "/outpost.goauthentik.io/start")
	http.Redirect(rw, r, authUrl+"?"+urlArgs.Encode(), http.StatusFound)
}

func (a *Application) redirect(rw http.ResponseWriter, r *http.Request) {
	redirect := a.proxyConfig.ExternalHost
	s, _ := a.sessions.Get(r, a.SessionName())
	redirectR, ok := s.Values[constants.SessionRedirect]
	if ok {
		redirect = redirectR.(string)
	}
	rd, ok := a.checkRedirectParam(r)
	if ok {
		redirect = rd
	}
	a.log.WithField("redirect", redirect).Trace("final redirect")
	http.Redirect(rw, r, redirect, http.StatusFound)
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
