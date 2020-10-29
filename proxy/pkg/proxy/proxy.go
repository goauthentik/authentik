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
	ipapi "github.com/oauth2-proxy/oauth2-proxy/pkg/apis/ip"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/apis/options"
	sessionsapi "github.com/oauth2-proxy/oauth2-proxy/pkg/apis/sessions"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/middleware"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/sessions"
	"github.com/oauth2-proxy/oauth2-proxy/pkg/upstream"
	"github.com/oauth2-proxy/oauth2-proxy/providers"

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

	redirectURL                *url.URL // the url to receive requests at
	whitelistDomains           []string
	provider                   providers.Provider
	sessionStore               sessionsapi.SessionStore
	ProxyPrefix                string
	serveMux                   http.Handler
	SetXAuthRequest            bool
	SetBasicAuth               bool
	PassUserHeaders            bool
	BasicAuthUserAttribute     string
	BasicAuthPasswordAttribute string
	PassAccessToken            bool
	SetAuthorization           bool
	PassAuthorization          bool
	PreferEmailToUser          bool
	skipAuthRegex              []string
	skipAuthPreflight          bool
	skipAuthStripHeaders       bool
	mainJwtBearerVerifier      *oidc.IDTokenVerifier
	extraJwtBearerVerifiers    []*oidc.IDTokenVerifier
	compiledRegex              []*regexp.Regexp
	templates                  *template.Template
	realClientIPParser         ipapi.RealClientIPParser

	sessionChain alice.Chain

	logger *log.Entry
}

// NewOAuthProxy creates a new instance of OAuthProxy from the options provided
func NewOAuthProxy(opts *options.Options) (*OAuthProxy, error) {
	logger := log.WithField("component", "proxy").WithField("client-id", opts.ClientID)
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
		realClientIPParser:      opts.GetRealClientIPParser(),
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

// splitHostPort separates host and port. If the port is not valid, it returns
// the entire input as host, and it doesn't check the validity of the host.
// Unlike net.SplitHostPort, but per RFC 3986, it requires ports to be numeric.
// *** taken from net/url, modified validOptionalPort() to accept ":*"
func splitHostPort(hostport string) (host, port string) {
	host = hostport

	colon := strings.LastIndexByte(host, ':')
	if colon != -1 && validOptionalPort(host[colon:]) {
		host, port = host[:colon], host[colon+1:]
	}

	if strings.HasPrefix(host, "[") && strings.HasSuffix(host, "]") {
		host = host[1 : len(host)-1]
	}

	return
}

// validOptionalPort reports whether port is either an empty string
// or matches /^:\d*$/
// *** taken from net/url, modified to accept ":*"
func validOptionalPort(port string) bool {
	if port == "" || port == ":*" {
		return true
	}
	if port[0] != ':' {
		return false
	}
	for _, b := range port[1:] {
		if b < '0' || b > '9' {
			return false
		}
	}
	return true
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
	redirect, err := p.GetRedirect(req)
	if err != nil {
		p.logger.Errorf("Error obtaining redirect: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	err = p.ClearSessionCookie(rw, req)
	if err != nil {
		p.logger.Errorf("Error clearing session cookie: %v", err)
		p.ErrorPage(rw, http.StatusInternalServerError, "Internal Server Error", err.Error())
		return
	}
	http.Redirect(rw, req, redirect, http.StatusFound)
}

// AuthenticateOnly checks whether the user is currently logged in
func (p *OAuthProxy) AuthenticateOnly(rw http.ResponseWriter, req *http.Request) {
	session, err := p.getAuthenticatedSession(rw, req)
	if err != nil {
		http.Error(rw, "unauthorized request", http.StatusUnauthorized)
		return
	}

	// we are authenticated
	p.addHeadersForProxying(rw, req, session)
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

	if p.SetBasicAuth {
		claims := Claims{}
		err := claims.FromIDToken(session.IDToken)
		if err != nil {
			log.WithError(err).Warning("Failed to parse IDToken")
		}

		userAttributes := claims.Proxy.UserAttributes
		var ok bool
		var password string
		if password, ok = userAttributes[p.BasicAuthPasswordAttribute]; !ok {
			password = ""
		}
		// Check if we should use email or a custom attribute as username
		var username string
		if username, ok = userAttributes[p.BasicAuthUserAttribute]; !ok {
			username = session.Email
		}
		authVal := b64.StdEncoding.EncodeToString([]byte(username + ":" + password))
		req.Header["Authorization"] = []string{fmt.Sprintf("Basic %s", authVal)}
	}
}

// stripAuthHeaders removes Auth headers for whitelisted routes from skipAuthRegex
func (p *OAuthProxy) stripAuthHeaders(req *http.Request) {
	if p.PassUserHeaders {
		req.Header.Del("X-Forwarded-User")
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
