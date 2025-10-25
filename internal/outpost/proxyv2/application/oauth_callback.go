package application

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"time"

	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
	"golang.org/x/oauth2"
)

func (a *Application) handleAuthCallback(rw http.ResponseWriter, r *http.Request) {
	state := a.stateFromRequest(r)
	if state == nil {
		a.log.Warning("invalid state")
		a.redirect(rw, r)
		return
	}
	claims, err := a.redeemCallback(r.URL, r.Context())
	if err != nil {
		a.log.WithError(err).Warning("failed to redeem code")
		a.redirect(rw, r)
		return
	}
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.WithError(err).Trace("failed to get session")
	}
	s.Options.MaxAge = int(time.Until(time.Unix(int64(claims.Exp), 0)).Seconds())
	s.Values[constants.SessionClaims] = claims
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session")
		rw.WriteHeader(400)
		return
	}
	a.redirect(rw, r)
}

func (a *Application) redeemCallback(u *url.URL, c context.Context) (*types.Claims, error) {
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
	var claims *types.Claims
	if err := idToken.Claims(&claims); err != nil {
		return nil, err
	}
	if claims.Proxy == nil {
		claims.Proxy = &types.ProxyClaims{}
	}
	claims.RawToken = jwt
	return claims, nil
}
