package application

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"strings"
)

type TokenResponse struct {
	AccessToken string `json:"access_token"`
	IDToken     string `json:"id_token"`
}

const JWTUsername = "goauthentik.io/token"

func (a *Application) attemptBasicAuth(username, password string) *Claims {
	if username == JWTUsername {
		res := a.attemptBearerAuth(password)
		if res != nil {
			return &res.Claims
		}
	}
	values := url.Values{
		"grant_type": []string{"client_credentials"},
		"client_id":  []string{a.oauthConfig.ClientID},
		"username":   []string{username},
		"password":   []string{password},
		"scope":      []string{strings.Join(a.oauthConfig.Scopes, " ")},
	}
	req, err := http.NewRequest("POST", a.endpoint.TokenURL, strings.NewReader(values.Encode()))
	if err != nil {
		a.log.WithError(err).Warning("failed to create token request")
		return nil
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := a.publicHostHTTPClient.Do(req)
	if err != nil {
		a.log.WithError(err).Warning("failed to send token request")
		return nil
	}
	defer func() {
		if err := res.Body.Close(); err != nil {
			a.log.WithError(err).Warning("failed to close response body")
		}
	}()

	if res.StatusCode > 200 {
		b, readErr := io.ReadAll(res.Body)
		if readErr != nil {
			b = []byte(readErr.Error())
		}
		a.log.WithError(err).WithField("body", string(b)).Warning("failed to send token request")
		return nil
	}

	var token TokenResponse
	err = json.NewDecoder(res.Body).Decode(&token)
	if err != nil {
		a.log.WithError(err).Warning("failed to parse token response")
		return nil
	}
	// Parse and verify ID Token payload.
	idToken, err := a.tokenVerifier.Verify(context.Background(), token.IDToken)
	if err != nil {
		a.log.WithError(err).Warning("failed to verify token")
		return nil
	}

	// Extract custom claims
	var claims *Claims
	if err := idToken.Claims(&claims); err != nil {
		a.log.WithError(err).Warning("failed to convert token to claims")
		return nil
	}
	if claims.Proxy == nil {
		claims.Proxy = &ProxyClaims{}
	}
	claims.RawToken = token.IDToken
	return claims
}
