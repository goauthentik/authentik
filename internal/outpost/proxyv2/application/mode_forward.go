package application

import (
	"fmt"
	"net/http"
	"strings"

	"goauthentik.io/internal/outpost/proxyv2/constants"
)

const (
	envoyPrefix   = "/outpost.goauthentik.io/auth/envoy"
	caddyPrefix   = "/outpost.goauthentik.io/auth/caddy"
	traefikPrefix = "/outpost.goauthentik.io/auth/traefik"
	nginxPrefix   = "/outpost.goauthentik.io/auth/nginx"
)

func (a *Application) configureForward() error {
	a.mux.HandleFunc(traefikPrefix, a.forwardHandleTraefik)
	a.mux.HandleFunc(caddyPrefix, a.forwardHandleCaddy)
	a.mux.HandleFunc(nginxPrefix, a.forwardHandleNginx)
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
	tr := r.Clone(r.Context())
	tr.URL = fwd
	if strings.EqualFold(fwd.Query().Get(CallbackSignature), "true") {
		a.log.Debug("handling OAuth Callback from querystring signature")
		a.handleAuthCallback(rw, tr)
		return
	} else if strings.EqualFold(fwd.Query().Get(LogoutSignature), "true") {
		a.log.Debug("handling OAuth Logout from querystring signature")
		a.handleSignOut(rw, r)
		return
	}
	// Check if we're authenticated, or the request path is on the allowlist
	claims, err := a.checkAuth(rw, r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	a.handleAuthStart(rw, r)
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	s, _ := a.sessions.Get(r, a.SessionName())
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = fwd.String()
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session")
		}
	}
}

func (a *Application) forwardHandleCaddy(rw http.ResponseWriter, r *http.Request) {
	a.log.WithField("header", r.Header).Trace("tracing headers for debug")
	// First check if we've got everything we need
	fwd, err := a.getTraefikForwardUrl(r)
	if err != nil {
		a.ReportMisconfiguration(r, fmt.Sprintf("Outpost %s (Provider %s) failed to detect a forward URL from Caddy", a.outpostName, a.proxyConfig.Name), map[string]interface{}{
			"provider": a.proxyConfig.Name,
			"outpost":  a.outpostName,
			"url":      r.URL.String(),
			"headers":  cleanseHeaders(r.Header),
		})
		http.Error(rw, "configuration error", http.StatusInternalServerError)
		return
	}
	tr := r.Clone(r.Context())
	tr.URL = fwd
	if strings.EqualFold(fwd.Query().Get(CallbackSignature), "true") {
		a.log.Debug("handling OAuth Callback from querystring signature")
		a.handleAuthCallback(rw, tr)
		return
	} else if strings.EqualFold(fwd.Query().Get(LogoutSignature), "true") {
		a.log.Debug("handling OAuth Logout from querystring signature")
		a.handleSignOut(rw, r)
		return
	}
	// Check if we're authenticated, or the request path is on the allowlist
	claims, err := a.checkAuth(rw, r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	a.handleAuthStart(rw, r)
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	s, _ := a.sessions.Get(r, a.SessionName())
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = fwd.String()
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session")
		}
	}
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

	claims, err := a.checkAuth(rw, r)
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

	s, _ := a.sessions.Get(r, a.SessionName())
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = fwd.String()
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session before redirect")
		}
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
	r.URL.Host = r.Host
	fwd := r.URL
	// Check if we're authenticated, or the request path is on the allowlist
	claims, err := a.checkAuth(rw, r)
	if claims != nil && err == nil {
		a.addHeaders(rw.Header(), claims)
		rw.Header().Set("User-Agent", r.Header.Get("User-Agent"))
		a.log.WithField("headers", rw.Header()).Trace("headers written to forward_auth")
		return
	} else if claims == nil && a.IsAllowlisted(fwd) {
		a.log.Trace("path can be accessed without authentication")
		return
	}
	a.handleAuthStart(rw, r)
	// set the redirect flag to the current URL we have, since we redirect
	// to a (possibly) different domain, but we want to be redirected back
	// to the application
	// X-Forwarded-Uri is only the path, so we need to build the entire URL
	s, _ := a.sessions.Get(r, a.SessionName())
	if _, redirectSet := s.Values[constants.SessionRedirect]; !redirectSet {
		s.Values[constants.SessionRedirect] = fwd.String()
		err = s.Save(r, rw)
		if err != nil {
			a.log.WithError(err).Warning("failed to save session before redirect")
		}
	}
}
