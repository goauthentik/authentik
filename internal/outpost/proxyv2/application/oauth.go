package application

import (
	"net/http"
	"net/url"
	"strings"

	"go.uber.org/zap"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const (
	redirectParam     = "rd"
	CallbackSignature = "X-authentik-auth-callback"
	LogoutSignature   = "X-authentik-logout"
)

func (a *Application) handleAuthStart(rw http.ResponseWriter, r *http.Request, fwd string) {
	state, err := a.createState(r, fwd)
	if err != nil {
		a.log.Warn("failed to create state", zap.Error(err))
		return
	}
	s, _ := a.sessions.Get(r, a.SessionName())
	err = s.Save(r, rw)
	if err != nil {
		a.log.Warn("failed to save session", zap.Error(err))
	}
	http.Redirect(rw, r, a.oauthConfig.AuthCodeURL(state), http.StatusFound)
}

func (a *Application) redirectToStart(rw http.ResponseWriter, r *http.Request) {
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.log.Warn("failed to decode session", zap.Error(err))
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
			a.log.Warn("Invalid redirect found", zap.String("url", r.URL.String()), zap.String("cd", dom))
			redirectUrl = a.proxyConfig.ExternalHost
		}
	}
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = redirectUrl
		err = s.Save(r, rw)
		if err != nil {
			a.log.Warn("failed to save session before redirect", zap.Error(err))
		}
	}

	urlArgs := url.Values{
		redirectParam: []string{redirectUrl},
	}
	authUrl := urlJoin(a.proxyConfig.ExternalHost, "/outpost.goauthentik.io/start")
	http.Redirect(rw, r, authUrl+"?"+urlArgs.Encode(), http.StatusFound)
}
