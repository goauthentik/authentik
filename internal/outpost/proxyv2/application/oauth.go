package application

import (
	"context"
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const (
	redirectParam     = "rd"
	CallbackSignature = "X-authentik-auth-callback"
	LogoutSignature   = "X-authentik-logout"
)

func (a *Application) handleAuthStart(rw http.ResponseWriter, r *http.Request, fwd string) {
	state, err := a.createState(r, rw, fwd)
	if err != nil {
		a.log.WithError(err).Warning("failed to create state")
		if !strings.HasPrefix(err.Error(), "failed to get session") {
			rw.WriteHeader(400)
			return
		}

		// Client has a cookie but we're unable to load the session from
		// storage (TMPDIR=/dev/shm). This can happen if the session file
		// was deleted due to container restart or session invalidation
		// (e.g., logout on auth server).
		//
		// Re-save an empty session and try again.

		session, err := a.sessions.Get(r, a.SessionName())
		if err != nil && !strings.HasSuffix(err.Error(), "no such file or directory") {
			a.log.WithError(err).Warning("failed to get session")
			rw.WriteHeader(400)
			return
		}
		err = a.sessions.Save(r, rw, session)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session")
			rw.WriteHeader(400)
			return
		}

		// The registry caches the previous attempt to open the session so it
		// needs to be cleared in order to get the session in createState().
		*r = *r.WithContext(context.Background())

		state, err = a.createState(r, rw, fwd)
		if err != nil {
			a.log.WithError(err).Warning("failed to create state on retry")
			rw.WriteHeader(400)
			return
		}
	}
	http.Redirect(rw, r, a.oauthConfig.AuthCodeURL(state), http.StatusFound)
}

func (a *Application) redirectToStart(rw http.ResponseWriter, r *http.Request) {
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.WithError(err).Warning("failed to decode session")
	}
	if r.Header.Get(constants.HeaderAuthorization) != "" && *a.proxyConfig.InterceptHeaderAuth {
		rw.WriteHeader(401)
		er := a.errorTemplates.Execute(rw, ErrorPageData{
			Title:       "Unauthenticated",
			Message:     "Due to 'Receive header authentication' being set, no redirect is performed.",
			ProxyPrefix: "/outpost.goauthentik.io",
		})
		if er != nil {
			http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
		}
	}

	redirectUrl := urlJoin(a.proxyConfig.ExternalHost, r.URL.Path)

	if a.Mode() == api.PROXYMODE_FORWARD_DOMAIN {
		dom := strings.TrimPrefix(*a.proxyConfig.CookieDomain, ".")
		// In forward_domain we only check that the current URL's host
		// ends with the cookie domain (remove the leading period if set)
		if !strings.HasSuffix(r.URL.Hostname(), dom) {
			a.log.WithField("url", r.URL.String()).WithField("cd", dom).Warning("Invalid redirect found")
			redirectUrl = a.proxyConfig.ExternalHost
		}
	}
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = redirectUrl
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session before redirect")
		}
	}

	urlArgs := url.Values{
		redirectParam: []string{redirectUrl},
	}
	authUrl := urlJoin(a.proxyConfig.ExternalHost, "/outpost.goauthentik.io/start")
	http.Redirect(rw, r, authUrl+"?"+urlArgs.Encode(), http.StatusFound)
}
