package application

import (
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"strings"

	"goauthentik.io/api"
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
	s, err := a.sessions.Get(r, constants.SeesionName)
	if err == nil {
		a.log.WithError(err).Warning("failed to decode session")
	}
	redirectUrl := r.URL.String()
	// simple way to copy the URL
	u, _ := url.Parse(redirectUrl)
	// In proxy and forward_single mode we only have one URL that we route on
	// if we somehow got here without that URL, make sure we're at least redirected back to it
	if a.Mode() == api.PROXYMODE_PROXY || a.Mode() == api.PROXYMODE_FORWARD_SINGLE {
		u.Host = a.proxyConfig.ExternalHost
	}
	if a.Mode() == api.PROXYMODE_FORWARD_DOMAIN {
		dom := strings.TrimPrefix(*a.proxyConfig.CookieDomain, ".")
		// In forward_domain we only check that the current URL's host
		// ends with the cookie domain (remove the leading period if set)
		if !strings.HasSuffix(r.URL.Hostname(), dom) {
			a.log.WithField("url", r.URL.String()).WithField("cd", dom).Warning("Invalid redirect found")
			redirectUrl = ""
		}
	}
	s.Values[constants.SessionRedirect] = redirectUrl
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session before redirect")
	}

	authUrl := urlJoin(a.proxyConfig.ExternalHost, "/akprox/start")
	http.Redirect(rw, r, authUrl, http.StatusFound)
}

// getClaims Get claims which are currently in session
// Returns an error if the session can't be loaded or the claims can't be parsed/type-cast
func (a *Application) getClaims(r *http.Request) (*Claims, error) {
	s, err := a.sessions.Get(r, constants.SeesionName)
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
