package application

import (
	"encoding/base32"
	"encoding/base64"
	"fmt"
	"net/http"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/securecookie"
	"github.com/mitchellh/mapstructure"
)

type OAuthState struct {
	SessionID string `json:"sid" mapstructure:"sid"`
	State     string `json:"state" mapstructure:"state"`
	Redirect  string `json:"redirect" mapstructure:"redirect"`
}

func (oas *OAuthState) GetExpirationTime() (*jwt.NumericDate, error) { return nil, nil }
func (oas *OAuthState) GetIssuedAt() (*jwt.NumericDate, error)       { return nil, nil }
func (oas *OAuthState) GetNotBefore() (*jwt.NumericDate, error)      { return nil, nil }
func (oas *OAuthState) GetIssuer() (string, error)                   { return "goauthentik.io/outpost", nil }
func (oas *OAuthState) GetSubject() (string, error)                  { return oas.State, nil }
func (oas *OAuthState) GetAudience() (jwt.ClaimStrings, error)       { return nil, nil }

var base32RawStdEncoding = base32.StdEncoding.WithPadding(base32.NoPadding)

func (a *Application) createState(r *http.Request) (string, error) {
	s, _ := a.sessions.Get(r, a.SessionName())
	if s.ID == "" {
		// Ensure session has an ID
		s.ID = base32RawStdEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
	}
	st := &OAuthState{
		State:     base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32)),
		SessionID: s.ID,
	}
	rd, ok := a.checkRedirectParam(r)
	if ok {
		a.log.WithField("rd", rd).Trace("Setting redirect")
		st.Redirect = rd
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
		a.log.WithError(err).Warning("failed to parse state jwt")
		return nil
	}
	claims := &OAuthState{}
	err = mapstructure.Decode(token.Claims, &claims)
	fmt.Printf("%+v\n", token.Claims)
	if err != nil {
		a.log.WithError(err).Warning("failed to mapdecode")
		return nil
	}
	s, _ := a.sessions.Get(r, a.SessionName())
	if claims.SessionID != s.ID {
		a.log.WithField("is", claims.SessionID).WithField("should", s.ID).Warning("mismatched session ID")
		return nil
	}
	return claims
}
