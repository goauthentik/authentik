package application

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"strings"

	"go.uber.org/zap"
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
		a.log.Warn("failed to create token request", zap.Error(err))
		return nil
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := a.publicHostHTTPClient.Do(req)
	if err != nil || res.StatusCode > 200 {
		b, err := io.ReadAll(res.Body)
		if err != nil {
			b = []byte(err.Error())
		}
		a.log.Warn("failed to send token request", zap.Error(err), zap.String("body", string(b)))
		return nil
	}
	var token TokenResponse
	err = json.NewDecoder(res.Body).Decode(&token)
	if err != nil {
		a.log.Warn("failed to parse token response", zap.Error(err))
		return nil
	}
	// Parse and verify ID Token payload.
	idToken, err := a.tokenVerifier.Verify(context.Background(), token.IDToken)
	if err != nil {
		a.log.Warn("failed to verify token", zap.Error(err))
		return nil
	}

	// Extract custom claims
	var claims *Claims
	if err := idToken.Claims(&claims); err != nil {
		a.log.Warn("failed to convert token to claims", zap.Error(err))
		return nil
	}
	if claims.Proxy == nil {
		claims.Proxy = &ProxyClaims{}
	}
	claims.RawToken = token.IDToken
	return claims
}
