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
	s.Values[constants.SessionRedirect] = redirectUrl
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session before redirect")
	}

	urlArgs := url.Values{
		"rd": []string{redirectUrl},
	}
	authUrl := urlJoin(a.proxyConfig.ExternalHost, "/outpost.goauthentik.io/start")
	http.Redirect(rw, r, authUrl+"?"+urlArgs.Encode(), http.StatusFound)
}

// getClaims Get claims which are currently in session
// Returns an error if the session can't be loaded or the claims can't be parsed/type-cast
func (a *Application) getClaims(r *http.Request) (*Claims, error) {
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		// err == user has no session/session is not valid, reject
		return nil, fmt.Errorf("invalid session")
	}
	claims, ok := s.Values[constants.SessionClaims]
	if claims == nil || !ok {
		// no claims saved, reject
		return nil, fmt.Errorf("invalid session")
	}
	c, ok := claims.(Claims)
	if !ok {
		return nil, fmt.Errorf("invalid session")
	}
	return &c, nil
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
