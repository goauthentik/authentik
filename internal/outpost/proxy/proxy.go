package proxy

import (
	b64 "encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"html/template"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	"github.com/coreos/go-oidc"
	"github.com/justinas/alice"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	sessionsapi "github.com/oauth2-proxy/oauth2-proxy/pkg/apis/sessions"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/middleware"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/sessions"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/upstream"
	"github.com/oauth2-proxy/oauth2-proxy/providers"
	"goauthentik.io/api"
	"goauthentik.io/internal/utils/web"

	log "github.com/sirupsen/logrus"
)

const (
	httpScheme  = "http"
	httpsScheme = "https"

	applicationJSON = "application/json"
)

var (
	// ErrNeedsLogin means the user should be redirected to the login page
	ErrNeedsLogin = errors.New("redirect to login page")

	// Used to check final redirects are not susceptible to open redirects.
	// Matches //, /\ and both of these with whitespace in between (eg / / or / \).
	invalidRedirectRegex = regexp.MustCompile(`[/\\](?:[\s\v]*|\.{1,2})[/\\]`)
)

// OAuthProxy is the main authentication proxy
type OAuthProxy struct {
	client *http.Client

	CookieSeed     string
	CookieName     string
	CSRFCookieName string
	CookieDomains  []string
	CookiePath     string
	CookieSecure   bool
	CookieHTTPOnly bool
	CookieExpire   time.Duration
	CookieRefresh  time.Duration
	CookieSameSite string

	RobotsPath        string
	SignInPath        string
	SignOutPath       string
	OAuthStartPath    string
	OAuthCallbackPath string
	AuthOnlyPath      string
	UserInfoPath      string

	endSessionEndpoint         string
	mode                       api.ProxyMode
	BasicAuthUserAttribute     string
	BasicAuthPasswordAttribute string
	ExternalHost               string

	redirectURL             *url.URL // the url to receive requests at
	whitelistDomains        []string
	provider                providers.Provider
	sessionStore            sessionsapi.SessionStore
	ProxyPrefix             string
	serveMux                http.Handler
	SetXAuthRequest         bool
	SetBasicAuth            bool
	PassUserHeaders         bool
	PassAccessToken         bool
	SetAuthorization        bool
	PassAuthorization       bool
	PreferEmailToUser       bool
	skipAuthRegex           []string
	skipAuthPreflight       bool
	skipAuthStripHeaders    bool
	mainJwtBearerVerifier   *oidc.IDTokenVerifier
	extraJwtBearerVerifiers []*oidc.IDTokenVerifier
	compiledRegex           []*regexp.Regexp
	templates               *template.Template

	sessionChain alice.Chain

	logger *log.Entry
}

// NewOAuthProxy creates a new instance of OAuthProxy from the options provided
func NewOAuthProxy(opts *options.Options, provider api.ProxyOutpostConfig, c *http.Client) (*OAuthProxy, error) {
	logger := log.WithField("logger", "authentik.outpost.proxy").WithField("provider", provider.Name)
	sessionStore, err := sessions.NewSessionStore(&opts.Session, &opts.Cookie)
	if err != nil {
		return nil, fmt.Errorf("error initialising session store: %v", err)
	}

	templates := getTemplates()
	proxyErrorHandler := upstream.NewProxyErrorHandler(templates.Lookup("error.html"), opts.ProxyPrefix)
	upstreamProxy, err := upstream.NewProxy(opts.UpstreamServers, opts.GetSignatureData(), proxyErrorHandler)
	if err != nil {
		return nil, fmt.Errorf("error initialising upstream proxy: %v", err)
	}

	for _, u := range opts.GetCompiledRegex() {
		logger.Printf("compiled skip-auth-regex => %q", u)
	}

	redirectURL := opts.GetRedirectURL()
	if redirectURL.Path == "" {
		redirectURL.Path = fmt.Sprintf("%s/callback", opts.ProxyPrefix)
	}

	logger.Printf("proxy instance configured for Client ID: %s", opts.ClientID)

	sessionChain := buildSessionChain(opts, sessionStore)

	return &OAuthProxy{
		client:         c,
		CookieName:     opts.Cookie.Name,
		CSRFCookieName: fmt.Sprintf("%v_%v", opts.Cookie.Name, "csrf"),
		CookieSeed:     opts.Cookie.Secret,
		CookieDomains:  opts.Cookie.Domains,
		CookiePath:     opts.Cookie.Path,
		CookieSecure:   opts.Cookie.Secure,
		CookieHTTPOnly: opts.Cookie.HTTPOnly,
		CookieExpire:   opts.Cookie.Expire,
		CookieRefresh:  opts.Cookie.Refresh,
		CookieSameSite: opts.Cookie.SameSite,

		mode:              *provider.Mode,
		RobotsPath:        "/robots.txt",
		SignInPath:        fmt.Sprintf("%s/sign_in", opts.ProxyPrefix),
		SignOutPath:       fmt.Sprintf("%s/sign_out", opts.ProxyPrefix),
		OAuthStartPath:    fmt.Sprintf("%s/start", opts.ProxyPrefix),
		OAuthCallbackPath: fmt.Sprintf("%s/callback", opts.ProxyPrefix),
		AuthOnlyPath:      fmt.Sprintf("%s/auth", opts.ProxyPrefix),
		UserInfoPath:      fmt.Sprintf("%s/userinfo", opts.ProxyPrefix),

		ProxyPrefix:             opts.ProxyPrefix,
		provider:                opts.GetProvider(),
		sessionStore:            sessionStore,
		serveMux:                upstreamProxy,
		redirectURL:             redirectURL,
		whitelistDomains:        opts.WhitelistDomains,
		skipAuthRegex:           opts.SkipAuthRegex,
		skipAuthPreflight:       opts.SkipAuthPreflight,
		skipAuthStripHeaders:    opts.SkipAuthStripHeaders,
		mainJwtBearerVerifier:   opts.GetOIDCVerifier(),
		extraJwtBearerVerifiers: opts.GetJWTBearerVerifiers(),
		compiledRegex:           opts.GetCompiledRegex(),
		SetXAuthRequest:         opts.SetXAuthRequest,
		SetBasicAuth:            opts.SetBasicAuth,
		PassUserHeaders:         opts.PassUserHeaders,
		PassAccessToken:         opts.PassAccessToken,
		SetAuthorization:        opts.SetAuthorization,
		PassAuthorization:       opts.PassAuthorization,
		PreferEmailToUser:       opts.PreferEmailToUser,
		templates:               templates,

		sessionChain: sessionChain,

		logger: logger,
	}, nil
}

func buildSessionChain(opts *options.Options, sessionStore sessionsapi.SessionStore) alice.Chain {
	chain := alice.New(middleware.NewScope())

	chain = chain.Append(middleware.NewStoredSessionLoader(&middleware.StoredSessionLoaderOptions{
		SessionStore:           sessionStore,
		RefreshPeriod:          opts.Cookie.Refresh,
		RefreshSessionIfNeeded: opts.GetProvider().RefreshSessionIfNeeded,
		ValidateSessionState:   opts.GetProvider().ValidateSessionState,
	}))

	return chain
}

// RobotsTxt disallows scraping pages from the OAuthProxy
func (p *OAuthProxy) RobotsTxt(rw http.ResponseWriter) {
	_, err := fmt.Fprintf(rw, "User-agent: *\nDisallow: /")
	if err != nil {
		p.logger.Printf("Error writing robots.txt: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	rw.WriteHeader(http.StatusOK)
}

// ErrorPage writes an error response
func (p *OAuthProxy) ErrorPage(rw http.ResponseWriter, code int, title string, message string) {
	rw.WriteHeader(code)
	t := struct {
		Title       string
		Message     string
		ProxyPrefix string
	}{
		Title:       fmt.Sprintf("%d %s", code, title),
		Message:     message,
		ProxyPrefix: p.ProxyPrefix,
	}
	err := p.templates.ExecuteTemplate(rw, "error.html", t)
	if err != nil {
		p.logger.Printf("Error rendering error.html template: %v", err)
		http.Error(rw, "Internal Server Error", http.StatusInternalServerError)
	}
}

// See https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching?hl=en
var noCacheHeaders = map[string]string{
	"Expires":         time.Unix(0, 0).Format(time.RFC1123),
	"Cache-Control":   "no-cache, no-store, must-revalidate, max-age=0",
	"X-Accel-Expires": "0", // https://www.nginx.com/resources/wiki/start/topics/examples/x-accel/
}

// prepareNoCache prepares headers for preventing browser caching.
func prepareNoCache(w http.ResponseWriter) {
	// Set NoCache headers
	for k, v := range noCacheHeaders {
		w.Header().Set(k, v)
	}
}

func (p *OAuthProxy) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	if req.URL.Path != p.AuthOnlyPath && strings.HasPrefix(req.URL.Path, p.ProxyPrefix) {
		prepareNoCache(rw)
	}
	rw.Header().Set("Server", "authentik-outpost")

	switch path := req.URL.Path; {
	case path == p.RobotsPath:
		p.RobotsTxt(rw)
	case p.IsWhitelistedRequest(req):
		p.SkipAuthProxy(rw, req)
	case path == p.SignInPath:
		p.OAuthStart(rw, req)
	case path == p.SignOutPath:
		p.SignOut(rw, req)
	case path == p.OAuthStartPath:
		p.OAuthStart(rw, req)
	case path == p.OAuthCallbackPath:
		p.OAuthCallback(rw, req)
	case path == p.AuthOnlyPath:
		p.AuthenticateOnly(rw, req)
	case path == p.UserInfoPath:
		p.UserInfo(rw, req)
	default:
		p.Proxy(rw, req)
	}
}

//UserInfo endpoint outputs session email and preferred username in JSON format
func (p *OAuthProxy) UserInfo(rw http.ResponseWriter, req *http.Request) {

	session, err := p.getAuthenticatedSession(rw, req)
	if err != nil {
		http.Error(rw, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}
	userInfo := struct {
		Email             string `json:"email"`
		PreferredUsername string `json:"preferredUsername,omitempty"`
	}{
		Email:             session.Email,
		PreferredUsername: session.PreferredUsername,
	}
	rw.Header().Set("Content-Type", "application/json")
	rw.WriteHeader(http.StatusOK)
	err = json.NewEncoder(rw).Encode(userInfo)
	if err != nil {
		p.logger.Printf("Error encoding user info: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
	}
}

// SignOut sends a response to clear the authentication cookie
func (p *OAuthProxy) SignOut(rw http.ResponseWriter, req *http.Request) {
	err := p.ClearSessionCookie(rw, req)
	if err != nil {
		p.logger.Errorf("Error clearing session cookie: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	http.Redirect(rw, req, p.endSessionEndpoint, http.StatusFound)
}

// AuthenticateOnly checks whether the user is currently logged in
func (p *OAuthProxy) AuthenticateOnly(rw http.ResponseWriter, req *http.Request) {
	session, err := p.getAuthenticatedSession(rw, req)
	if err != nil {
		if p.mode == api.PROXYMODE_FORWARD_SINGLE || p.mode == api.PROXYMODE_FORWARD_DOMAIN {
			if _, ok := req.URL.Query()["nginx"]; ok {
				rw.WriteHeader(401)
				return
			}
			if _, ok := req.URL.Query()["traefik"]; ok {
				host := ""
				// Optional suffix, which is appended to the URL
				suffix := ""
				if p.mode == api.PROXYMODE_FORWARD_SINGLE {
					host = web.GetHost(req)
				} else if p.mode == api.PROXYMODE_FORWARD_DOMAIN {
					host = p.ExternalHost
					// set the ?rd flag to the current URL we have, since we redirect
					// to a (possibly) different domain, but we want to be redirected back
					// to the application
					v := url.Values{
						// see https://doc.traefik.io/traefik/middlewares/forwardauth/
						// X-Forwarded-Uri is only the path, so we need to build the entire URL
						"rd": []string{fmt.Sprintf(
							"%s://%s%s",
							req.Header.Get("X-Forwarded-Proto"),
							req.Header.Get("X-Forwarded-Host"),
							req.Header.Get("X-Forwarded-Uri"),
						)},
					}
					suffix = fmt.Sprintf("?%s", v.Encode())
				}
				proto := req.Header.Get("X-Forwarded-Proto")
				if proto != "" {
					proto = proto + ":"
				}
				rdFinal := fmt.Sprintf("%s//%s%s%s", proto, host, p.OAuthStartPath, suffix)
				p.logger.WithField("url", rdFinal).Debug("Redirecting to login")
				http.Redirect(rw, req, rdFinal, http.StatusTemporaryRedirect)
				return
			}
		}
		http.Error(rw, "unauthorized request", http.StatusUnauthorized)
		return
	}
	// we are authenticated
	p.addHeadersForProxying(rw, req, session)
	if p.mode == api.PROXYMODE_FORWARD_SINGLE || p.mode == api.PROXYMODE_FORWARD_DOMAIN {
		for headerKey, headers := range req.Header {
			for _, value := range headers {
				rw.Header().Set(headerKey, value)
			}
		}
	}
	rw.WriteHeader(http.StatusAccepted)
}

// SkipAuthProxy proxies whitelisted requests and skips authentication
func (p *OAuthProxy) SkipAuthProxy(rw http.ResponseWriter, req *http.Request) {
	if p.skipAuthStripHeaders {
		p.stripAuthHeaders(req)
	}
	p.serveMux.ServeHTTP(rw, req)
}

// Proxy proxies the user request if the user is authenticated else it prompts
// them to authenticate
func (p *OAuthProxy) Proxy(rw http.ResponseWriter, req *http.Request) {
	session, err := p.getAuthenticatedSession(rw, req)
	switch err {
	case nil:
		// we are authenticated
		p.addHeadersForProxying(rw, req, session)
		p.serveMux.ServeHTTP(rw, req)

	case ErrNeedsLogin:
		// we need to send the user to a login screen
		if isAjax(req) {
			// no point redirecting an AJAX request
			p.ErrorJSON(rw, http.StatusUnauthorized)
			return
		}

		p.OAuthStart(rw, req)

	default:
		// unknown error
		p.logger.Errorf("Unexpected internal error: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError,
			"Internal Error", "Internal Error")
	}

}

// getAuthenticatedSession checks whether a user is authenticated and returns a session object and nil error if so
// Returns nil, ErrNeedsLogin if user needs to login.
// Set-Cookie headers may be set on the response as a side-effect of calling this method.
func (p *OAuthProxy) getAuthenticatedSession(rw http.ResponseWriter, req *http.Request) (*sessionsapi.SessionState, error) {
	var session *sessionsapi.SessionState

	getSession := p.sessionChain.Then(http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
		session = middleware.GetRequestScope(req).Session
	}))
	getSession.ServeHTTP(rw, req)

	if session == nil {
		return nil, ErrNeedsLogin
	}

	return session, nil
}

// addHeadersForProxying adds the appropriate headers the request / response for proxying
func (p *OAuthProxy) addHeadersForProxying(rw http.ResponseWriter, req *http.Request, session *sessionsapi.SessionState) {
	// req is the request that is forwarded to the upstream server
	// rw is the response writer that goes back to the client
	req.Header["X-Forwarded-User"] = []string{session.User}
	if session.Email != "" {
		req.Header["X-Forwarded-Email"] = []string{session.Email}
	}

	if session.PreferredUsername != "" {
		req.Header["X-Forwarded-Preferred-Username"] = []string{session.PreferredUsername}
		req.Header["X-Auth-Username"] = []string{session.PreferredUsername}
	} else {
		req.Header.Del("X-Forwarded-Preferred-Username")
		req.Header.Del("X-Auth-Username")
	}

	claims := Claims{}
	err := claims.FromIDToken(session.IDToken)
	if err != nil {
		log.WithError(err).Warning("Failed to parse IDToken")
	}
	// Set groups in header
	groups := strings.Join(claims.Groups, "|")
	req.Header["X-Auth-Groups"] = []string{groups}

	userAttributes := claims.Proxy.UserAttributes
	// Attempt to set basic auth based on user's attributes
	if p.SetBasicAuth {
		var ok bool
		var password string
		if password, ok = userAttributes[p.BasicAuthPasswordAttribute].(string); !ok {
			password = ""
		}
		// Check if we should use email or a custom attribute as username
		var username string
		if username, ok = userAttributes[p.BasicAuthUserAttribute].(string); !ok {
			username = session.Email
		}
		authVal := b64.StdEncoding.EncodeToString([]byte(username + ":" + password))
		p.logger.WithField("username", username).Trace("setting http basic auth")
		req.Header["Authorization"] = []string{fmt.Sprintf("Basic %s", authVal)}
	}
	// Check if user has additional headers set that we should sent
	if additionalHeaders, ok := userAttributes["additionalHeaders"].(map[string]interface{}); ok {
		p.logger.WithField("headers", additionalHeaders).Trace("setting additional headers")
		if additionalHeaders == nil {
			return
		}
		for key, value := range additionalHeaders {
			req.Header.Set(key, toString(value))
		}
	}
}

// stripAuthHeaders removes Auth headers for whitelisted routes from skipAuthRegex
func (p *OAuthProxy) stripAuthHeaders(req *http.Request) {
	if p.PassUserHeaders {
		req.Header.Del("X-Forwarded-User")
		req.Header.Del("X-Auth-Groups")
		req.Header.Del("X-Forwarded-Email")
		req.Header.Del("X-Forwarded-Preferred-Username")
	}

	if p.PassAccessToken {
		req.Header.Del("X-Forwarded-Access-Token")
	}

	if p.PassAuthorization {
		req.Header.Del("Authorization")
	}
}

// isAjax checks if a request is an ajax request
func isAjax(req *http.Request) bool {
	acceptValues := req.Header.Values("Accept")
	const ajaxReq = applicationJSON
	for _, v := range acceptValues {
		if v == ajaxReq {
			return true
		}
	}
	return false
}

// ErrorJSON returns the error code with an application/json mime type
func (p *OAuthProxy) ErrorJSON(rw http.ResponseWriter, code int) {
	rw.Header().Set("Content-Type", applicationJSON)
	rw.WriteHeader(code)
}
