package application

import (
	"fmt"
	"net/http"
	"time"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const HeaderAuthorization = "Authorization"
const AuthBearer = "Bearer "

// checkAuth Get claims which are currently in session
// Returns an error if the session can't be loaded or the claims can't be parsed/type-cast
func (a *Application) checkAuth(rw http.ResponseWriter, r *http.Request) (*Claims, error) {
	c := a.getClaimsFromSession(r)
	if c != nil {
		return c, nil
	}

	if rw == nil {
		return nil, fmt.Errorf("no response writer")
	}
	// Check TTL cache
	c = a.getClaimsFromCache(r)
	if c != nil {
		return c, nil
	}
	// Check bearer token if set
	bearer := a.checkAuthHeaderBearer(r)
	if bearer != "" {
		a.log.Trace("checking bearer token")
		tc := a.attemptBearerAuth(r, bearer)
		if tc != nil {
			return a.saveAndCacheClaims(rw, r, tc.Claims)
		}
		a.log.Trace("no/invalid bearer token")
	}
	// Check basic auth if set
	username, password, basicSet := r.BasicAuth()
	if basicSet {
		a.log.Trace("checking basic auth")
		tc := a.attemptBasicAuth(username, password)
		if tc != nil {
			return a.saveAndCacheClaims(rw, r, *tc)
		}
		a.log.Trace("no/invalid basic auth")
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

func (a *Application) getClaimsFromCache(r *http.Request) *Claims {
	key := r.Header.Get(HeaderAuthorization)
	item := a.authHeaderCache.Get(key)
	if item != nil && !item.IsExpired() {
		v := item.Value()
		return &v
	}
	return nil
}

func (a *Application) saveAndCacheClaims(rw http.ResponseWriter, r *http.Request, claims Claims) (*Claims, error) {
	s, _ := a.sessions.Get(r, constants.SessionName)

	s.Values[constants.SessionClaims] = claims
	err := s.Save(r, rw)
	if err != nil {
		return nil, err
	}

	key := r.Header.Get(HeaderAuthorization)
	item := a.authHeaderCache.Get(key)
	// Don't set when the key is already found
	if item == nil {
		a.authHeaderCache.Set(key, claims, time.Second*60)
	}
	r.Header.Del(HeaderAuthorization)
	return &claims, nil
}
