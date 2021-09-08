package application

import (
	"fmt"
	"net/http"
	"strconv"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func (a *Application) redirectToStart(rw http.ResponseWriter, r *http.Request) {
	authUrl := fmt.Sprintf("%s/akprox/start", a.proxyConfig.ExternalHost)
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

func contains(s []string, e string) bool {
	for _, a := range s {
		if a == e {
			return true
		}
	}
	return false
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
