package application

import (
	"fmt"
	"net/http"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const HeaderAuthorization = "Authorization"
const AuthBearer = "Bearer "
const AuthBasic = "Basic "

// checkAuth Get claims which are currently in session
// Returns an error if the session can't be loaded or the claims can't be parsed/type-cast
func (a *Application) checkAuth(rw http.ResponseWriter, r *http.Request) (*Claims, error) {
	s, _ := a.sessions.Get(r, constants.SessionName)

	c := a.getClaimsFromSession(r)
	if c != nil {
		return c, nil
	}

	if rw == nil {
		return nil, fmt.Errorf("no response writer")
	}
	// Check bearer token if set
	bearer := a.checkAuthHeaderBearer(r)
	if bearer != "" {
		a.log.Trace("checking bearer token")
		tc := a.attemptBearerAuth(r, bearer)
		if tc != nil {
			s.Values[constants.SessionClaims] = tc.Claims
			err := s.Save(r, rw)
			if err != nil {
				return nil, err
			}
			r.Header.Del(HeaderAuthorization)
			return &tc.Claims, nil
		}
	}
	// Check basic auth if set
	username, password, basicSet := r.BasicAuth()
	if basicSet {
		a.log.Trace("checking basic auth")
		tc := a.attemptBasicAuth(username, password)
		if tc != nil {
			s.Values[constants.SessionClaims] = tc
			err := s.Save(r, rw)
			if err != nil {
				return nil, err
			}
			r.Header.Del(HeaderAuthorization)
			return tc, nil
		}
	}

	return nil, fmt.Errorf("failed to get claims from session")
}

func (a *Application) getClaimsFromSession(r *http.Request) *Claims {
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		// err == user has no session/session is not valid, reject
		return nil
	}
	claims, ok := s.Values[constants.SessionClaims]
	if claims == nil || !ok {
		// no claims saved, reject
		return nil
	}
	c, ok := claims.(Claims)
	if !ok {
		return nil
	}
	return &c
}
