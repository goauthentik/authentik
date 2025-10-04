package application

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// checkAuth Get claims which are currently in session
// Returns an error if the session can't be loaded or the claims can't be parsed/type-cast
func (a *Application) checkAuth(rw http.ResponseWriter, r *http.Request) (*types.Claims, error) {
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
		tc := a.attemptBearerAuth(bearer)
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

func (a *Application) getClaimsFromSession(r *http.Request) *types.Claims {
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		// err == user has no session/session is not valid, reject
		return nil
	}
	claims, ok := s.Values[constants.SessionClaims]
	if claims == nil || !ok {
		// no claims saved, reject
		return nil
	}

	// Try direct cast first (when using filesystem store which stores Claims struct directly)
	if c, ok := claims.(types.Claims); ok {
		return &c
	}

	// Try pointer cast (when using filesystem store with pointer)
	if c, ok := claims.(*types.Claims); ok {
		return c
	}

	// Claims from PostgreSQL storage are deserialized as map[string]interface{} from JSONB
	claimsMap, ok := claims.(map[string]interface{})
	if !ok {
		return nil
	}

	// Convert map back to Claims struct using JSON marshaling
	jsonData, err := json.Marshal(claimsMap)
	if err != nil {
		return nil
	}

	var c types.Claims
	if err := json.Unmarshal(jsonData, &c); err != nil {
		return nil
	}

	return &c
}

func (a *Application) getClaimsFromCache(r *http.Request) *types.Claims {
	key := r.Header.Get(constants.HeaderAuthorization)
	item := a.authHeaderCache.Get(key)
	if item != nil && !item.IsExpired() {
		v := item.Value()
		return &v
	}
	return nil
}

func (a *Application) saveAndCacheClaims(rw http.ResponseWriter, r *http.Request, claims types.Claims) (*types.Claims, error) {
	s, _ := a.sessions.Get(r, a.SessionName())

	s.Values[constants.SessionClaims] = claims
	err := s.Save(r, rw)
	if err != nil {
		return nil, err
	}

	key := r.Header.Get(constants.HeaderAuthorization)
	item := a.authHeaderCache.Get(key)
	// Don't set when the key is already found
	if item == nil {
		a.authHeaderCache.Set(key, claims, time.Second*60)
	}
	r.Header.Del(constants.HeaderAuthorization)
	return &claims, nil
}
