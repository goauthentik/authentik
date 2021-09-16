package application

import (
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strconv"

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
