package application

import (
	"net/http"
	"net/url"
	"strings"
)

type TokenResponse struct {
	AccessToken string `json:"access_token"`
}

func (a *Application) attemptBasicAuth(username, password string) *Claims {
	values := url.Values{
		"grant_types": []string{"client_credentials"},
		"client_id":   []string{a.oauthConfig.ClientID},
		"username":    []string{username},
		"password":    []string{password},
	}
	req, err := http.NewRequest("POST", a.endpoint.TokenURL, strings.NewReader(values.Encode()))
	if err != nil {
		a.log.WithError(err).Warning("failed to create token request")
		return nil
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := a.httpClient.Do(req)
	if err != nil {
		a.log.WithError(err).Warning("failed to send token request")
		return nil
	}
	return nil
}
