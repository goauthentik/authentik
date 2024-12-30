package application

import (
	"encoding/json"
	"net/http"
	"net/url"
	"strings"

	"go.uber.org/zap"
	"goauthentik.io/internal/config"
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

func (a *Application) attemptBearerAuth(token string) *TokenIntrospectionResponse {
	values := url.Values{
		"client_id":     []string{a.oauthConfig.ClientID},
		"client_secret": []string{a.oauthConfig.ClientSecret},
		"token":         []string{token},
	}
	req, err := http.NewRequest("POST", a.endpoint.TokenIntrospection, strings.NewReader(values.Encode()))
	if err != nil {
		a.log.Warn("failed to create introspection request", zap.Error(err))
		return nil
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := a.publicHostHTTPClient.Do(req)
	if err != nil || res.StatusCode > 200 {
		a.log.Warn("failed to send introspection request", zap.Error(err))
		return nil
	}
	intro := TokenIntrospectionResponse{}
	err = json.NewDecoder(res.Body).Decode(&intro)
	if err != nil {
		a.log.Warn("failed to parse introspection response", zap.Error(err))
		return nil
	}
	if !intro.Active {
		a.log.Warn("token is not active")
		return nil
	}
	intro.RawToken = token
	a.log.Debug("successfully introspected bearer token", config.Trace())
	return &intro
}
