package application

import (
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"strings"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func urlPathSet(originalUrl string, newPath string) string {
	u, err := url.Parse(originalUrl)
	if err != nil {
		return originalUrl
	}
	u.Path = newPath
	return u.String()
}

func urlJoin(originalUrl string, newPath string) string {
	u, err := url.Parse(originalUrl)
	if err != nil {
		return originalUrl
	}
	u.Path = path.Join(u.Path, newPath)
	return u.String()
}

func (a *Application) redirectToStart(rw http.ResponseWriter, r *http.Request) {
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		a.log.WithError(err).Warning("failed to decode session")
	}

	if r.Header.Get(constants.HeaderNoRedirect) == "true" {
		rw.WriteHeader(401)
		er := a.errorTemplates.Execute(rw, ErrorPageData{
			Title:       "Unauthenticated",
			Message:     fmt.Sprintf("Due to '%s' being set, no redirect is performed.", constants.HeaderNoRedirect),
			ProxyPrefix: "/outpost.goauthentik.io",
		})
		if er != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	} else if strings.HasPrefix(r.UserAgent(), "VLC") {
		rw.WriteHeader(401)
		er := a.errorTemplates.Execute(rw, ErrorPageData{
			Title:       "Unauthenticated",
			Message:     fmt.Sprintf("Due to '%s' being set, no redirect is performed.", constants.HeaderNoRedirect),
			ProxyPrefix: "/outpost.goauthentik.io",
		})
		if er != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	}

	redirectUrl := urlPathSet(a.proxyConfig.ExternalHost, r.URL.Path)

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
	rd, ok := a.checkRedirectParam(r)
	if ok {
		redirect = rd
	}
	s, _ := a.sessions.Get(r, constants.SessionName)
	redirectR, ok := s.Values[constants.SessionRedirect]
	if ok {
		redirect = redirectR.(string)
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
