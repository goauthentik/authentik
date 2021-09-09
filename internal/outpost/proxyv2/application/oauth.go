package application

import (
	"encoding/base64"
	"net/http"

	"github.com/gorilla/securecookie"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func (a *Application) handleRedirect(rw http.ResponseWriter, r *http.Request) {
	state := base64.RawStdEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
	s, _ := a.sessions.Get(r, constants.SeesionName)
	s.Values[constants.SessionOAuthState] = state
	err := s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session")
	}
	http.Redirect(rw, r, a.oauthConfig.AuthCodeURL(state), http.StatusFound)
}

func (a *Application) handleCallback(rw http.ResponseWriter, r *http.Request) {
	s, _ := a.sessions.Get(r, constants.SeesionName)
	state, ok := s.Values[constants.SessionOAuthState]
	if !ok {
		a.log.Warning("No state saved in session")
		http.Redirect(rw, r, a.proxyConfig.ExternalHost, http.StatusFound)
		return
	}
	claims, err := a.redeemCallback(r, state.(string))
	if err != nil {
		a.log.WithError(err).Warning("failed to redeem code")
		rw.WriteHeader(400)
		// To prevent the user from just refreshing and cause more errors, delete
		// the state from the session
		delete(s.Values, constants.SessionOAuthState)
		err := s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session")
			rw.WriteHeader(400)
			return
		}
		return
	}
	s.Options.MaxAge = claims.Exp / 1000
	s.Values[constants.SessionClaims] = &claims
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session")
		rw.WriteHeader(400)
		return
	}
	redirect := a.proxyConfig.ExternalHost
	redirectR, ok := s.Values[constants.SessionRedirect]
	if ok {
		redirect = redirectR.(string)
	}
	http.Redirect(rw, r, redirect, http.StatusFound)
}
