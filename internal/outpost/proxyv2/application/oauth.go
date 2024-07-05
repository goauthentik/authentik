package application

import (
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
		ext.Scheme = ""
		if !strings.Contains(u.String(), ext.String()) {
			a.log.WithField("url", u.String()).WithField("ext", ext.String()).Warning("redirect URI did not contain external host")
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

func (a *Application) handleAuthStart(rw http.ResponseWriter, r *http.Request, fwd string) {
	state, err := a.createState(r, fwd)
	if err != nil {
		a.log.WithError(err).Warning("failed to create state")
		return
	}
	s, _ := a.sessions.Get(r, a.SessionName())
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session")
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
