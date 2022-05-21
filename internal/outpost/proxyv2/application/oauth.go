package application

import (
	"encoding/base64"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/gorilla/securecookie"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const (
	redirectParam = "rd"
)

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
		if !strings.Contains(u.String(), a.proxyConfig.ExternalHost) {
			a.log.WithField("url", u.String()).WithField("ext", a.proxyConfig.ExternalHost).Warning("redirect URI did not contain external host")
			return "", false
		}
	} else {
		if !strings.HasSuffix(u.Host, *a.proxyConfig.CookieDomain) {
			a.log.WithField("host", u.Host).WithField("dom", *a.proxyConfig.CookieDomain).Warning("redirect URI Host was not included in cookie domain")
			return "", false
		}
	}
	return u.String(), true
}

func (a *Application) handleRedirect(rw http.ResponseWriter, r *http.Request) {
	newState := base64.RawURLEncoding.EncodeToString(securecookie.GenerateRandomKey(32))
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		s.Values[constants.SessionOAuthState] = []string{}
	}
	state, ok := s.Values[constants.SessionOAuthState].([]string)
	if !ok {
		s.Values[constants.SessionOAuthState] = []string{}
		state = []string{}
	}
	rd, ok := a.checkRedirectParam(r)
	if ok {
		s.Values[constants.SessionRedirect] = rd
		a.log.WithField("rd", rd).Trace("Setting redirect")
	}
	s.Values[constants.SessionOAuthState] = append(state, newState)
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session")
	}
	http.Redirect(rw, r, a.oauthConfig.AuthCodeURL(newState), http.StatusFound)
}

func (a *Application) handleCallback(rw http.ResponseWriter, r *http.Request) {
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		a.log.WithError(err).Trace("failed to get session")
	}
	state, ok := s.Values[constants.SessionOAuthState]
	if !ok {
		a.log.Warning("No state saved in session")
		http.Redirect(rw, r, a.proxyConfig.ExternalHost, http.StatusFound)
		return
	}
	claims, err := a.redeemCallback(r, state.([]string))
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
	s.Options.MaxAge = int(time.Until(time.Unix(int64(claims.Exp), 0)).Seconds())
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
	a.log.WithField("redirect", redirect).Trace("final redirect")
	http.Redirect(rw, r, redirect, http.StatusFound)
}
