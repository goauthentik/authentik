package application

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

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
		s.Values[constants.SessionClaims] = tc.Claims
		err := s.Save(r, rw)
		if err != nil {
			return nil, err
		}
		r.Header.Del("Authorization")
		return &tc.Claims, nil
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

func (a *Application) checkAuthHeaderBearer(r *http.Request) string {
	auth := r.Header.Get("Authorization")
	if auth == "" {
		return ""
	}
	parts := strings.SplitN(auth, " ", 2)
	if len(parts) < 2 || !strings.EqualFold(parts[0], "Bearer") {
		return ""
	}
	return parts[1]
}

type TokenIntrospectionResponse struct {
	Claims
	Active   bool   `json:"active"`
	ClientID string `json:"client_id"`
}

func (a *Application) attemptBearerAuth(r *http.Request, token string) *TokenIntrospectionResponse {
	values := url.Values{
		"client_id":     []string{a.oauthConfig.ClientID},
		"client_secret": []string{a.oauthConfig.ClientSecret},
		"token":         []string{token},
	}
	req, err := http.NewRequest("POST", a.endpoint.TokenIntrospection, strings.NewReader(values.Encode()))
	if err != nil {
		a.log.WithError(err).Warning("failed to create introspection request")
		return nil
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := a.httpClient.Do(req)
	if err != nil {
		a.log.WithError(err).Warning("failed to send introspection request")
		return nil
	}
	intro := TokenIntrospectionResponse{}
	err = json.NewDecoder(res.Body).Decode(&intro)
	if err != nil {
		a.log.WithError(err).Warning("failed to parse introspection response")
		return nil
	}
	if !intro.Active {
		a.log.Warning("token is not active")
		return nil
	}
	intro.RawToken = token
	a.log.Trace("successfully introspected bearer token")
	return &intro
}
