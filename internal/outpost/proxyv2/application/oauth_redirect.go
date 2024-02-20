package application

import (
	"encoding/base64"
	"fmt"
	"net/http"

	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/securecookie"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

type OAuthState struct {
	State    string `json:"state"`
	Redirect string `json:"redirect"`
}

func (oas *OAuthState) GetExpirationTime() (*jwt.NumericDate, error) { return nil, nil }
func (oas *OAuthState) GetIssuedAt() (*jwt.NumericDate, error)       { return nil, nil }
func (oas *OAuthState) GetNotBefore() (*jwt.NumericDate, error)      { return nil, nil }
func (oas *OAuthState) GetIssuer() (string, error)                   { return "goauthentik.io/outpost", nil }
func (oas *OAuthState) GetSubject() (string, error)                  { return oas.State, nil }
func (oas *OAuthState) GetAudience() (jwt.ClaimStrings, error)       { return nil, nil }

func (a *Application) createState(r *http.Request) (string, error) {
	st := &OAuthState{
		State: base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32)),
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
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.WithError(err).Trace("failed to get session")
		return nil
	}
	stateJwt, ok := s.Values[constants.SessionOAuthState]
	if !ok {
		return nil
	}
	token, err := jwt.Parse(stateJwt.(string), func(token *jwt.Token) (interface{}, error) {
		// Don't forget to validate the alg is what you expect:
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return a.proxyConfig.CookieSecret, nil
	})
	if err != nil {
		a.log.WithError(err).Warning("failed to parse state jwt")
		return nil
	}
	if claims, ok := token.Claims.(*OAuthState); ok {
		return claims
	}
	return nil
}
