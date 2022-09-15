package application

import (
	"context"
	"fmt"
	"net/http"

	log "github.com/sirupsen/logrus"
	"golang.org/x/oauth2"
)

func (a *Application) redeemCallback(r *http.Request, states []string) (*Claims, error) {
	state := r.URL.Query().Get("state")
	if len(states) < 1 {
		return nil, fmt.Errorf("no states")
	}
	found := false
	for _, fstate := range states {
		if fstate == state {
			found = true
		}
	}
	a.log.WithFields(log.Fields{
		"states":   states,
		"expected": state,
		"found":    found,
	}).Trace("tracing states")
	if !found {
		return nil, fmt.Errorf("invalid state")
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
	claims.RawToken = rawIDToken
	return claims, nil
}
