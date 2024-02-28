package application

import (
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/api/v3"
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

func (a *Application) handleAuthStart(rw http.ResponseWriter, r *http.Request) {
	state, err := a.createState(r)
	if err != nil {
		a.log.WithError(err).Warning("failed to create state")
		return
	}
	http.Redirect(rw, r, a.oauthConfig.AuthCodeURL(state), http.StatusFound)
}
