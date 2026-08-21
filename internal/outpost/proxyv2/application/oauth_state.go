package application

import (
	"encoding/base32"
	"encoding/base64"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/securecookie"
	"github.com/mitchellh/mapstructure"
	api "goauthentik.io/packages/client-go"
)

type OAuthState struct {
	Issuer    string `json:"iss" mapstructure:"iss"`
	SessionID string `json:"sid" mapstructure:"sid"`
	State     string `json:"state" mapstructure:"state"`
	Redirect  string `json:"redirect" mapstructure:"redirect"`
}

func (oas *OAuthState) GetExpirationTime() (*jwt.NumericDate, error) { return nil, nil }
func (oas *OAuthState) GetIssuedAt() (*jwt.NumericDate, error)       { return nil, nil }
func (oas *OAuthState) GetNotBefore() (*jwt.NumericDate, error)      { return nil, nil }
func (oas *OAuthState) GetIssuer() (string, error)                   { return oas.Issuer, nil }
func (oas *OAuthState) GetSubject() (string, error)                  { return oas.State, nil }
func (oas *OAuthState) GetAudience() (jwt.ClaimStrings, error)       { return nil, nil }

var base32RawStdEncoding = base32.StdEncoding.WithPadding(base32.NoPadding)

// Validate that the given redirect parameter (?rd=...) is valid and can be used
// For proxy/forward_single this checks that if the `rd` param has a Hostname (and is a full URL)
// the hostname matches what's configured, or no hostname must be given
// For forward_domain this checks if the domain of the URL in `rd` ends with the configured domain
func (a *Application) checkRedirectParam(r *http.Request) (string, bool) {
	rd := r.URL.Query().Get(redirectParam)
	if rd == "" {
		return "", false
	}
	u, err := url.Parse(rd)
	if err != nil {
		a.log.WithError(err).Warning("Failed to parse redirect URL")
		return "", false
	}
	// Check to make sure we only redirect to allowed places
	if a.Mode() == api.PROXYMODE_PROXY || a.Mode() == api.PROXYMODE_FORWARD_SINGLE {
		ext, err := url.Parse(a.proxyConfig.ExternalHost)
		if err != nil {
			return "", false
		}
		// Either hostname needs to match the configured domain, or host name must be empty for just a path
		if u.Host == "" {
			u.Host = ext.Host
			u.Scheme = ext.Scheme
		}
		if u.Host != ext.Host {
			a.log.WithField("url", u.String()).WithField("ext", ext.String()).Warning("redirect URI did not contain external host")
			return "", false
		}
	} else {
		if !strings.HasSuffix(u.Hostname(), *a.proxyConfig.CookieDomain) {
			a.log.WithField("host", u.Hostname()).WithField("dom", *a.proxyConfig.CookieDomain).Warning("redirect URI Hostname was not included in cookie domain")
			return "", false
		}
	}
	return u.String(), true
}

func (a *Application) createState(r *http.Request, w http.ResponseWriter, fwd string) (string, error) {
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		// The client presented a session cookie but the backing session could not
		// be loaded: it was erased on sign-out, or lost because the outpost
		// restarted while storing sessions in a tmpfs (TMPDIR=/dev/shm).
		//
		// Reset the stale session in place and continue with a new one.
		// a.sessions.Get() memoises both the session and the error in the
		// request-scoped registry, so re-fetching would only hand back this very
		// same object with the dead ID still set, skipping the regeneration below
		// and minting a state JWT for a session that is never written to the
		// store. Options is left alone: it is shared with every other Get() in
		// this request and Save() below depends on its MaxAge.
		a.log.WithError(err).Debug("discarding stale session")
		s.ID = ""
		s.IsNew = true
		s.Values = map[any]any{}
	}
	if s.ID == "" {
		// Ensure session has an ID
		s.ID = base32RawStdEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
		// Save the session immediately so it persists
		err := s.Save(r, w)
		if err != nil {
			return "", fmt.Errorf("failed to save session: %w", err)
		}
	}
	st := &OAuthState{
		Issuer:    fmt.Sprintf("goauthentik.io/outpost/%s", a.proxyConfig.GetClientId()),
		State:     base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32)),
		SessionID: s.ID,
		Redirect:  fwd,
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, st)
	tokenString, err := token.SignedString([]byte(a.proxyConfig.GetCookieSecret()))
	if err != nil {
		return "", err
	}
	return tokenString, nil
}

func (a *Application) stateFromRequest(rw http.ResponseWriter, r *http.Request) *OAuthState {
	stateJwt := r.URL.Query().Get("state")
	token, err := jwt.Parse(stateJwt, func(token *jwt.Token) (any, error) {
		// Don't forget to validate the alg is what you expect:
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(a.proxyConfig.GetCookieSecret()), nil
	})
	if err != nil {
		a.log.WithError(err).Warning("failed to parse state jwt")
		return nil
	}
	iss, err := token.Claims.GetIssuer()
	if err != nil {
		a.log.WithError(err).Warning("state jwt without issuer")
		return nil
	}
	if iss != fmt.Sprintf("goauthentik.io/outpost/%s", a.proxyConfig.GetClientId()) {
		a.log.WithField("issuer", iss).Warning("invalid state jwt issuer")
		return nil
	}
	claims := &OAuthState{}
	err = mapstructure.Decode(token.Claims, &claims)
	if err != nil {
		a.log.WithError(err).Warning("failed to mapdecode")
		return nil
	}
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.WithError(err).Warning("failed to get session")
		// Delete the stale session cookie if it exists
		a.discardSession(rw, r, s)
		return nil
	}
	if claims.SessionID != s.ID {
		a.log.WithField("is", claims.SessionID).WithField("should", s.ID).Warning("mismatched session ID")
		return nil
	}
	return claims
}
