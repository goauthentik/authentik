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
	"go.uber.org/zap"
	"goauthentik.io/api/v3"
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
		a.log.Warn("Failed to parse redirect URL", zap.Error(err))
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
			a.log.Warn("redirect URI did not contain external host", zap.String("url", u.String()), zap.String("ext", ext.String()))
			return "", false
		}
	} else {
		if !strings.HasSuffix(u.Host, *a.proxyConfig.CookieDomain) {
			a.log.Warn("redirect URI Host was not included in cookie domain", zap.String("host", u.Host), zap.String("dom", *a.proxyConfig.CookieDomain))
			return "", false
		}
	}
	return u.String(), true
}

func (a *Application) createState(r *http.Request, fwd string) (string, error) {
	s, _ := a.sessions.Get(r, a.SessionName())
	if s.ID == "" {
		// Ensure session has an ID
		s.ID = base32RawStdEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
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

func (a *Application) stateFromRequest(r *http.Request) *OAuthState {
	stateJwt := r.URL.Query().Get("state")
	token, err := jwt.Parse(stateJwt, func(token *jwt.Token) (interface{}, error) {
		// Don't forget to validate the alg is what you expect:
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(a.proxyConfig.GetCookieSecret()), nil
	})
	if err != nil {
		a.log.Warn("failed to parse state jwt", zap.Error(err))
		return nil
	}
	iss, err := token.Claims.GetIssuer()
	if err != nil {
		a.log.Warn("state jwt without issuer", zap.Error(err))
		return nil
	}
	if iss != fmt.Sprintf("goauthentik.io/outpost/%s", a.proxyConfig.GetClientId()) {
		a.log.Warn("invalid state jwt issuer", zap.String("issuer", iss))
		return nil
	}
	claims := &OAuthState{}
	err = mapstructure.Decode(token.Claims, &claims)
	if err != nil {
		a.log.Warn("failed to mapdecode", zap.Error(err))
		return nil
	}
	s, _ := a.sessions.Get(r, a.SessionName())
	if claims.SessionID != s.ID {
		a.log.Warn("mismatched session ID", zap.String("is", claims.SessionID), zap.String("should", s.ID))
		return nil
	}
	return claims
}
