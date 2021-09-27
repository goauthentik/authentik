package application

import (
	"fmt"
	"net/http"
	"net/url"

	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/utils/web"
)

func (a *Application) configureForward() error {
	a.mux.HandleFunc("/akprox/auth", func(rw http.ResponseWriter, r *http.Request) {
		if _, ok := r.URL.Query()["traefik"]; ok {
			a.forwardHandleTraefik(rw, r)
			return
		}
		a.forwardHandleNginx(rw, r)
	})
	a.mux.HandleFunc("/akprox/auth/traefik", a.forwardHandleTraefik)
	a.mux.HandleFunc("/akprox/auth/nginx", a.forwardHandleNginx)
	return nil
}

func (a *Application) forwardHandleTraefik(rw http.ResponseWriter, r *http.Request) {
	claims, err := a.getClaims(r)
	if claims != nil && err == nil {
		a.addHeaders(r, claims)
		copyHeadersToResponse(rw, r)
		return
	} else if claims == nil && a.IsAllowlisted(r) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	host := ""
	s, _ := a.sessions.Get(r, constants.SeesionName)
	// Optional suffix, which is appended to the URL
	if *a.proxyConfig.Mode == api.PROXYMODE_FORWARD_SINGLE {
		host = web.GetHost(r)
	} else if *a.proxyConfig.Mode == api.PROXYMODE_FORWARD_DOMAIN {
		eh, _ := url.Parse(a.proxyConfig.ExternalHost)
		host = eh.Host
	}
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// see https://doc.traefik.io/traefik/middlewares/forwardauth/
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	s.Values[constants.SessionRedirect] = fmt.Sprintf(
		"%s://%s%s",
		r.Header.Get("X-Forwarded-Proto"),
		r.Header.Get("X-Forwarded-Host"),
		r.Header.Get("X-Forwarded-Uri"),
	)
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session before redirect")
	}
	proto := r.Header.Get("X-Forwarded-Proto")
	if proto != "" {
		proto = proto + ":"
	}
	rdFinal := fmt.Sprintf("%s//%s%s", proto, host, "/akprox/start")
	a.log.WithField("url", rdFinal).Debug("Redirecting to login")
	http.Redirect(rw, r, rdFinal, http.StatusTemporaryRedirect)
}

func (a *Application) forwardHandleNginx(rw http.ResponseWriter, r *http.Request) {
	claims, err := a.getClaims(r)
	if claims != nil && err == nil {
		a.addHeaders(r, claims)
		copyHeadersToResponse(rw, r)
		rw.WriteHeader(200)
		return
	} else if claims == nil && a.IsAllowlisted(r) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	http.Error(rw, "unauthorized request", http.StatusUnauthorized)
}
