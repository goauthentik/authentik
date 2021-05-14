package proxy

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	sessionsapi "github.com/oauth2-proxy/oauth2-proxy/pkg/apis/sessions"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/encryption"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/ip"
)

// GetRedirectURI returns the redirectURL that the upstream OAuth Provider will
// redirect clients to once authenticated
func (p *OAuthProxy) GetRedirectURI(host string) string {
	// default to the request Host if not set
	if p.redirectURL.Host != "" {
		return p.redirectURL.String()
	}
	u := *p.redirectURL
	if u.Scheme == "" {
		if p.CookieSecure {
			u.Scheme = httpsScheme
		} else {
			u.Scheme = httpScheme
		}
	}
	u.Host = host
	return u.String()
}

func (p *OAuthProxy) redeemCode(ctx context.Context, host, code string) (s *sessionsapi.SessionState, err error) {
	if code == "" {
		return nil, errors.New("missing code")
	}
	redirectURI := p.GetRedirectURI(host)
	s, err = p.provider.Redeem(ctx, redirectURI, code)
	if err != nil {
		return
	}

	if s.Email == "" {
		s.Email, err = p.provider.GetEmailAddress(ctx, s)
	}

	if s.PreferredUsername == "" {
		s.PreferredUsername, err = p.provider.GetPreferredUsername(ctx, s)
		if err != nil && err.Error() == "not implemented" {
			err = nil
		}
	}

	if s.User == "" {
		s.User, err = p.provider.GetUserName(ctx, s)
		if err != nil && err.Error() == "not implemented" {
			err = nil
		}
	}
	return
}

// GetRedirect reads the query parameter to get the URL to redirect clients to
// once authenticated with the OAuthProxy
func (p *OAuthProxy) GetRedirect(req *http.Request) (redirect string, err error) {
	err = req.ParseForm()
	if err != nil {
		return
	}

	redirect = req.Header.Get("X-Auth-Request-Redirect")
	if req.Form.Get("rd") != "" {
		redirect = req.Form.Get("rd")
	}
	if !p.IsValidRedirect(redirect) {
		// Use RequestURI to preserve ?query
		redirect = req.URL.RequestURI()
		if strings.HasPrefix(redirect, p.ProxyPrefix) {
			redirect = "/"
		}
	}

	return
}

// IsValidRedirect checks whether the redirect URL is whitelisted
func (p *OAuthProxy) IsValidRedirect(redirect string) bool {
	switch {
	case redirect == "":
		// The user didn't specify a redirect, should fallback to `/`
		return false
	case strings.HasPrefix(redirect, "/") && !strings.HasPrefix(redirect, "//") && !invalidRedirectRegex.MatchString(redirect):
		return true
	case strings.HasPrefix(redirect, "http://") || strings.HasPrefix(redirect, "https://"):
		redirectURL, err := url.Parse(redirect)
		if err != nil {
			p.logger.Printf("Rejecting invalid redirect %q: scheme unsupported or missing", redirect)
			return false
		}
		redirectHostname := redirectURL.Hostname()

		for _, domain := range p.whitelistDomains {
			domainHostname, domainPort := splitHostPort(strings.TrimLeft(domain, "."))
			if domainHostname == "" {
				continue
			}

			if (redirectHostname == domainHostname) || (strings.HasPrefix(domain, ".") && strings.HasSuffix(redirectHostname, domainHostname)) {
				// the domain names match, now validate the ports
				// if the whitelisted domain's port is '*', allow all ports
				// if the whitelisted domain contains a specific port, only allow that port
				// if the whitelisted domain doesn't contain a port at all, only allow empty redirect ports ie http and https
				redirectPort := redirectURL.Port()
				if (domainPort == "*") ||
					(domainPort == redirectPort) ||
					(domainPort == "" && redirectPort == "") {
					return true
				}
			}
		}

		p.logger.Printf("Rejecting invalid redirect %q: domain / port not in whitelist", redirect)
		return false
	default:
		p.logger.Printf("Rejecting invalid redirect %q: not an absolute or relative URL", redirect)
		return false
	}
}

// IsWhitelistedRequest is used to check if auth should be skipped for this request
func (p *OAuthProxy) IsWhitelistedRequest(req *http.Request) bool {
	isPreflightRequestAllowed := p.skipAuthPreflight && req.Method == "OPTIONS"
	return isPreflightRequestAllowed || p.IsWhitelistedPath(req.URL.Path)
}

// IsWhitelistedPath is used to check if the request path is allowed without auth
func (p *OAuthProxy) IsWhitelistedPath(path string) bool {
	for _, u := range p.compiledRegex {
		if u.MatchString(path) {
			return true
		}
	}
	return false
}

// OAuthStart starts the OAuth2 authentication flow
func (p *OAuthProxy) OAuthStart(rw http.ResponseWriter, req *http.Request) {
	prepareNoCache(rw)
	nonce, err := encryption.Nonce()
	if err != nil {
		p.logger.Errorf("Error obtaining nonce: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	p.SetCSRFCookie(rw, req, nonce)
	redirect, err := p.GetRedirect(req)
	if err != nil {
		p.logger.Errorf("Error obtaining redirect: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	redirectURI := p.GetRedirectURI(req.Host)
	http.Redirect(rw, req, p.provider.GetLoginURL(redirectURI, fmt.Sprintf("%v:%v", nonce, redirect)), http.StatusFound)
}

// OAuthCallback is the OAuth2 authentication flow callback that finishes the
// OAuth2 authentication flow
func (p *OAuthProxy) OAuthCallback(rw http.ResponseWriter, req *http.Request) {
	remoteAddr := ip.GetClientString(p.realClientIPParser, req, true)

	// finish the oauth cycle
	err := req.ParseForm()
	if err != nil {
		p.logger.Errorf("Error while parsing OAuth2 callback: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	errorString := req.Form.Get("error")
	if errorString != "" {
		p.logger.Errorf("Error while parsing OAuth2 callback: %s", errorString)
		p.ErrorPage(rw, http.StatusForbidden, "Permission Denied", errorString)
		return
	}

	session, err := p.redeemCode(req.Context(), req.Host, req.Form.Get("code"))
	if err != nil {
		p.logger.Errorf("Error redeeming code during OAuth2 callback: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", "Internal Error")
		return
	}

	s := strings.SplitN(req.Form.Get("state"), ":", 2)
	if len(s) != 2 {
		p.logger.Error("Error while parsing OAuth2 state: invalid length")
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", "Invalid State")
		return
	}
	nonce := s[0]
	redirect := s[1]
	c, err := req.Cookie(p.CSRFCookieName)
	if err != nil {
		p.logger.WithField("user", session.Email).WithField("status", "AuthFailure").Info("Invalid authentication via OAuth2: unable to obtain CSRF cookie")
		p.ErrorPage(rw, http.StatusForbidden, "Permission Denied", err.Error())
		return
	}
	p.ClearCSRFCookie(rw, req)
	if c.Value != nonce {
		p.logger.WithField("user", session.Email).WithField("status", "AuthFailure").Info("Invalid authentication via OAuth2: CSRF token mismatch, potential attack")
		p.ErrorPage(rw, http.StatusForbidden, "Permission Denied", "CSRF Failed")
		return
	}

	if !p.IsValidRedirect(redirect) {
		redirect = "/"
	}

	// set cookie, or deny
	if p.provider.ValidateGroup(session.Email) {
		p.logger.WithField("user", session.Email).WithField("status", "AuthFailure").Infof("Authenticated via OAuth2: %s", session)
		err := p.SaveSession(rw, req, session)
		if err != nil {
			p.logger.Printf("Error saving session state for %s: %v", remoteAddr, err)
			p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
			return
		}
		http.Redirect(rw, req, redirect, http.StatusFound)
	} else {
		p.logger.WithField("user", session.Email).WithField("status", "AuthFailure").Info("Invalid authentication via OAuth2: unauthorized")
		p.ErrorPage(rw, http.StatusForbidden, "Permission Denied", "Invalid Account")
	}
}
