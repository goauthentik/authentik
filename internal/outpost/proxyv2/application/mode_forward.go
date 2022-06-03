package application

import (
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/utils/web"
)

const (
	envoyPrefix = "/outpost.goauthentik.io/auth/envoy"
)

func (a *Application) configureForward() error {
	a.mux.HandleFunc("/outpost.goauthentik.io/auth", func(rw http.ResponseWriter, r *http.Request) {
		if _, ok := r.URL.Query()["traefik"]; ok {
			a.forwardHandleTraefik(rw, r)
			return
		}
		a.forwardHandleNginx(rw, r)
	})
	a.mux.HandleFunc("/outpost.goauthentik.io/auth/traefik", a.forwardHandleTraefik)
	a.mux.HandleFunc("/outpost.goauthentik.io/auth/nginx", a.forwardHandleNginx)
	a.mux.PathPrefix(envoyPrefix).HandlerFunc(a.forwardHandleEnvoy)
	return nil
}

func (a *Application) forwardHandleTraefik(rw http.ResponseWriter, r *http.Request) {
	a.log.WithField("header", r.Header).Trace("tracing headers for debug")
	// First check if we've got everything we need
	fwd, err := a.getTraefikForwardUrl(r)
	if err != nil {
		a.ReportMisconfiguration(r, fmt.Sprintf("Outpost %s (Provider %s) failed to detect a forward URL from Traefik", a.outpostName, a.proxyConfig.Name), map[string]interface{}{
			"provider": a.proxyConfig.Name,
			"outpost":  a.outpostName,
			"url":      r.URL.String(),
			"headers":  cleanseHeaders(r.Header),
		})
		http.Error(rw, "configuration error", http.StatusInternalServerError)
		return
	}

	claims, err := a.getClaims(r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	if strings.HasPrefix(r.Header.Get("X-Forwarded-Uri"), "/outpost.goauthentik.io") {
		a.log.WithField("url", r.URL.String()).Trace("path begins with /outpost.goauthentik.io, allowing access")
		return
	}
	host := ""
	s, _ := a.sessions.Get(r, constants.SessionName)
	// Optional suffix, which is appended to the URL
	if *a.proxyConfig.Mode.Get() == api.PROXYMODE_FORWARD_SINGLE {
		host = web.GetHost(r)
	} else if *a.proxyConfig.Mode.Get() == api.PROXYMODE_FORWARD_DOMAIN {
		eh, err := url.Parse(a.proxyConfig.ExternalHost)
		if err != nil {
			a.log.WithField("host", a.proxyConfig.ExternalHost).WithError(err).Warning("invalid external_host")
		} else {
			host = eh.Host
		}
	}
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	s.Values[constants.SessionRedirect] = fwd.String()
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session before redirect")
	}

	proto := r.Header.Get("X-Forwarded-Proto")
	if proto != "" {
		proto = proto + ":"
	}
	rdFinal := fmt.Sprintf("%s//%s%s", proto, host, "/outpost.goauthentik.io/start")
	a.log.WithField("url", rdFinal).Debug("Redirecting to login")
	http.Redirect(rw, r, rdFinal, http.StatusTemporaryRedirect)
}

func (a *Application) forwardHandleNginx(rw http.ResponseWriter, r *http.Request) {
	a.log.WithField("header", r.Header).Trace("tracing headers for debug")
	fwd, err := a.getNginxForwardUrl(r)
	if err != nil {
		a.ReportMisconfiguration(r, fmt.Sprintf("Outpost %s (Provider %s) failed to detect a forward URL from nginx", a.outpostName, a.proxyConfig.Name), map[string]interface{}{
			"provider": a.proxyConfig.Name,
			"outpost":  a.outpostName,
			"url":      r.URL.String(),
			"headers":  cleanseHeaders(r.Header),
		})
		http.Error(rw, "configuration error", http.StatusInternalServerError)
		return
	}

	claims, err := a.getClaims(r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		rw.WriteHeader(200)
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}

	s, _ := a.sessions.Get(r, constants.SessionName)
	s.Values[constants.SessionRedirect] = fwd.String()
	err = s.Save(r, rw)
	if err != nil {
		a.log.WithError(err).Warning("failed to save session before redirect")
	}

	if fwd.String() != r.URL.String() {
		if strings.HasPrefix(fwd.Path, "/outpost.goauthentik.io") {
			a.log.WithField("url", r.URL.String()).Trace("path begins with /outpost.goauthentik.io, allowing access")
			return
		}
	}
	http.Error(rw, "unauthorized request", http.StatusUnauthorized)
}

func (a *Application) forwardHandleEnvoy(rw http.ResponseWriter, r *http.Request) {
	a.log.WithField("header", r.Header).Trace("tracing headers for debug")
	r.URL.Path = strings.TrimPrefix(r.URL.Path, envoyPrefix)
	fwd := r.URL

	claims, err := a.getClaims(r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	if strings.HasPrefix(r.URL.Path, "/outpost.goauthentik.io") {
		a.log.WithField("url", r.URL.String()).Trace("path begins with /outpost.goauthentik.io, allowing access")
		return
	}
	host := ""
	s, _ := a.sessions.Get(r, constants.SessionName)
	// Optional suffix, which is appended to the URL
	if *a.proxyConfig.Mode.Get() == api.PROXYMODE_FORWARD_SINGLE {
		host = web.GetHost(r)
	} else if *a.proxyConfig.Mode.Get() == api.PROXYMODE_FORWARD_DOMAIN {
		eh, err := url.Parse(a.proxyConfig.ExternalHost)
		if err != nil {
			a.log.WithField("host", a.proxyConfig.ExternalHost).WithError(err).Warning("invalid external_host")
		} else {
			host = eh.Host
		}
	}
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = fwd.String()
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session before redirect")
		}
	}
	rdFinal := fmt.Sprintf("//%s%s", host, "/outpost.goauthentik.io/start")
	a.log.WithField("url", rdFinal).Debug("Redirecting to login")
	http.Redirect(rw, r, rdFinal, http.StatusTemporaryRedirect)
}
