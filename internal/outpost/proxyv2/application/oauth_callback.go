package application

import (
	"context"
	"fmt"
	"net/http"

	"golang.org/x/oauth2"
)

func (a *Application) redeemCallback(r *http.Request, shouldState string) (*Claims, error) {
	state := r.URL.Query().Get("state")
	if state == "" || state != shouldState {
		return nil, fmt.Errorf("blank/invalid state")
	}

	code := r.URL.Query().Get("code")
	if code == "" {
		return nil, fmt.Errorf("blank code")
	}

	ctx := context.WithValue(r.Context(), oauth2.HTTPClient, a.httpClient)
	// Verify state and errors.
	oauth2Token, err := a.oauthConfig.Exchange(ctx, code)
	if err != nil {
		return nil, err
	}

	// Extract the ID Token from OAuth2 token.
	rawIDToken, ok := oauth2Token.Extra("id_token").(string)
	if !ok {
		return nil, fmt.Errorf("missing id_token")
	}

	a.log.WithField("id_token", rawIDToken).Trace("id_token")

	// Parse and verify ID Token payload.
	idToken, err := a.tokenVerifier.Verify(ctx, rawIDToken)
	if err != nil {
		return nil, err
	}

	// Extract custom claims
	var claims *Claims
	if err := idToken.Claims(&claims); err != nil {
		return nil, err
	}
	return claims, nil
}
