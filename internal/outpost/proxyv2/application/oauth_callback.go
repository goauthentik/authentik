package application

import (
	"context"
	"fmt"
	"net/url"

	log "github.com/sirupsen/logrus"
	"golang.org/x/oauth2"
)

func (a *Application) redeemCallback(savedState string, u *url.URL, c context.Context) (*Claims, error) {
	state := u.Query().Get("state")
	a.log.WithFields(log.Fields{
		"states":   savedState,
		"expected": state,
	}).Trace("tracing states")
	if savedState != state {
		return nil, fmt.Errorf("invalid state")
	}

	code := u.Query().Get("code")
	if code == "" {
		return nil, fmt.Errorf("blank code")
	}

	ctx := context.WithValue(c, oauth2.HTTPClient, a.publicHostHTTPClient)
	// Verify state and errors.
	oauth2Token, err := a.oauthConfig.Exchange(ctx, code)
	if err != nil {
		return nil, err
	}

	jwt := oauth2Token.AccessToken
	a.log.WithField("jwt", jwt).Trace("access_token")

	// Parse and verify ID Token payload.
	idToken, err := a.tokenVerifier.Verify(ctx, jwt)
	if err != nil {
		return nil, err
	}

	// Extract custom claims
	var claims *Claims
	if err := idToken.Claims(&claims); err != nil {
		return nil, err
	}
	if claims.Proxy == nil {
		claims.Proxy = &ProxyClaims{}
	}
	claims.RawToken = jwt
	return claims, nil
}
