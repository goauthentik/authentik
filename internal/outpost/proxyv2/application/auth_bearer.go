package application

import (
	"encoding/json"
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func (a *Application) checkAuthHeaderBearer(r *http.Request) string {
	auth := r.Header.Get(constants.HeaderAuthorization)
	if auth == "" {
		return ""
	}
	if len(auth) < len(constants.AuthBearer) || !strings.EqualFold(auth[:len(constants.AuthBearer)], constants.AuthBearer) {
		return ""
	}
	return auth[len(constants.AuthBearer):]
}

type TokenIntrospectionResponse struct {
	Claims
	Scope    string `json:"scope"`
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
	if err != nil || res.StatusCode > 200 {
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
