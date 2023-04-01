package application

import (
	"context"
	"crypto/sha256"
	"crypto/tls"
	"encoding/gob"
	"fmt"
	"html/template"
	"net/http"
	"net/url"
	"path"
	"regexp"
	"strings"
	"time"

	"github.com/coreos/go-oidc"
	"github.com/getsentry/sentry-go"
	sentryhttp "github.com/getsentry/sentry-go/http"
	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"github.com/jellydator/ttlcache/v3"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/hs256"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
	"goauthentik.io/internal/outpost/proxyv2/templates"
	"goauthentik.io/internal/utils/web"
	"golang.org/x/oauth2"
)

type Application struct {
	Host                 string
	Cert                 *tls.Certificate
	UnauthenticatedRegex []*regexp.Regexp

	endpoint      OIDCEndpoint
	oauthConfig   oauth2.Config
	tokenVerifier *oidc.IDTokenVerifier
	outpostName   string
	sessionName   string

	sessions             sessions.Store
	proxyConfig          api.ProxyOutpostConfig
	httpClient           *http.Client
	publicHostHTTPClient *http.Client

	log *log.Entry
	mux *mux.Router
	ak  *ak.APIController
	srv Server

	errorTemplates  *template.Template
	authHeaderCache *ttlcache.Cache[string, Claims]
}

type Server interface {
	API() *ak.APIController
	Apps() []*Application
	CryptoStore() *ak.CryptoStore
}

func NewApplication(p api.ProxyOutpostConfig, c *http.Client, server Server) (*Application, error) {
	gob.Register(Claims{})
	muxLogger := log.WithField("logger", "authentik.outpost.proxyv2.application").WithField("name", p.Name)

	externalHost, err := url.Parse(p.ExternalHost)
	if err != nil {
		return nil, fmt.Errorf("failed to parse URL, skipping provider")
	}

	var ks oidc.KeySet
	if contains(p.OidcConfiguration.IdTokenSigningAlgValuesSupported, "HS256") {
		ks = hs256.NewKeySet(*p.ClientSecret)
	} else {
		ctx := context.WithValue(context.Background(), oauth2.HTTPClient, c)
		ks = oidc.NewRemoteKeySet(ctx, p.OidcConfiguration.JwksUri)
	}

	redirectUri, _ := url.Parse(p.ExternalHost)
	redirectUri.Path = path.Join(redirectUri.Path, "/outpost.goauthentik.io/callback")
	redirectUri.RawQuery = url.Values{
		CallbackSignature: []string{"true"},
	}.Encode()

	managed := false
	if m := server.API().Outpost.Managed.Get(); m != nil {
		managed = *m == "goauthentik.io/outposts/embedded"
	}
	// Configure an OpenID Connect aware OAuth2 client.
	endpoint := GetOIDCEndpoint(
		p,
		server.API().Outpost.Config["authentik_host"].(string),
		managed,
	)

	verifier := oidc.NewVerifier(endpoint.Issuer, ks, &oidc.Config{
		ClientID:             *p.ClientId,
		SupportedSigningAlgs: []string{"RS256", "HS256"},
	})

	oauth2Config := oauth2.Config{
		ClientID:     *p.ClientId,
		ClientSecret: *p.ClientSecret,
		RedirectURL:  redirectUri.String(),
		Endpoint:     endpoint.Endpoint,
		Scopes:       p.ScopesToRequest,
	}
	mux := mux.NewRouter()

	// Save cookie name, based on hashed client ID
	h := sha256.New()
	bs := string(h.Sum([]byte(*p.ClientId)))
	sessionName := fmt.Sprintf("authentik_proxy_%s", bs[:8])

	a := &Application{
		Host:                 externalHost.Host,
		log:                  muxLogger,
		outpostName:          server.API().Outpost.Name,
		sessionName:          sessionName,
		endpoint:             endpoint,
		oauthConfig:          oauth2Config,
		tokenVerifier:        verifier,
		proxyConfig:          p,
		httpClient:           c,
		publicHostHTTPClient: web.NewHostInterceptor(c, server.API().Outpost.Config["authentik_host"].(string)),
		mux:                  mux,
		errorTemplates:       templates.GetTemplates(),
		ak:                   server.API(),
		authHeaderCache:      ttlcache.New(ttlcache.WithDisableTouchOnHit[string, Claims]()),
		srv:                  server,
	}
	go a.authHeaderCache.Start()
	a.sessions = a.getStore(p, externalHost)
	mux.Use(web.NewLoggingHandler(muxLogger, func(l *log.Entry, r *http.Request) *log.Entry {
		c := a.getClaimsFromSession(r)
		if c == nil {
			return l
		}
		if c.PreferredUsername != "" {
			return l.WithField("user", c.PreferredUsername)
		}
		return l.WithField("user", c.Sub)
	}))
	mux.Use(func(inner http.Handler) http.Handler {
		return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
			c := a.getClaimsFromSession(r)
			user := ""
			if c != nil {
				user = c.PreferredUsername
				hub := sentry.GetHubFromContext(r.Context())
				if hub == nil {
					hub = sentry.CurrentHub()
				}
				hub.Scope().SetUser(sentry.User{
					Username:  user,
					ID:        c.Sub,
					IPAddress: r.RemoteAddr,
				})
			}
			before := time.Now()
			inner.ServeHTTP(rw, r)
			after := time.Since(before)
			metrics.Requests.With(prometheus.Labels{
				"outpost_name": a.outpostName,
				"type":         "app",
				"method":       r.Method,
				"host":         web.GetHost(r),
			}).Observe(float64(after))
		})
	})
	if server.API().GlobalConfig.ErrorReporting.Enabled {
		mux.Use(sentryhttp.New(sentryhttp.Options{}).Handle)
	}
	mux.Use(func(inner http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if strings.EqualFold(r.URL.Query().Get(CallbackSignature), "true") {
				a.log.Debug("handling OAuth Callback from querystring signature")
				a.handleAuthCallback(w, r)
			} else if strings.EqualFold(r.URL.Query().Get(LogoutSignature), "true") {
				a.log.Debug("handling OAuth Logout from querystring signature")
				a.handleSignOut(w, r)
			} else {
				inner.ServeHTTP(w, r)
			}
		})
	})

	mux.HandleFunc("/outpost.goauthentik.io/start", a.handleAuthStart)
	mux.HandleFunc("/outpost.goauthentik.io/callback", a.handleAuthCallback)
	mux.HandleFunc("/outpost.goauthentik.io/sign_out", a.handleSignOut)
	switch *p.Mode {
	case api.PROXYMODE_PROXY:
		err = a.configureProxy()
	case api.PROXYMODE_FORWARD_SINGLE:
		fallthrough
	case api.PROXYMODE_FORWARD_DOMAIN:
		err = a.configureForward()
	}
	if err != nil {
		return nil, fmt.Errorf("failed to configure application mode: %w", err)
	}

	if kp := p.Certificate.Get(); kp != nil {
		err := server.CryptoStore().AddKeypair(*kp)
		if err != nil {
			return nil, fmt.Errorf("failed to initially fetch certificate: %w", err)
		}
		a.Cert = server.CryptoStore().Get(*kp)
	}

	if *p.SkipPathRegex != "" {
		a.UnauthenticatedRegex = make([]*regexp.Regexp, 0)
		for _, regex := range strings.Split(*p.SkipPathRegex, "\n") {
			re, err := regexp.Compile(regex)
			if err != nil {
				//TODO: maybe create event for this?
				a.log.WithError(err).Warning("failed to compile SkipPathRegex")
				continue
			} else {
				a.UnauthenticatedRegex = append(a.UnauthenticatedRegex, re)
			}
		}
	}
	return a, nil
}

func (a *Application) Mode() api.ProxyMode {
	return *a.proxyConfig.Mode
}

func (a *Application) HasQuerySignature(r *http.Request) bool {
	if strings.EqualFold(r.URL.Query().Get(CallbackSignature), "true") {
		return true
	}
	if strings.EqualFold(r.URL.Query().Get(LogoutSignature), "true") {
		return true
	}
	return false
}

func (a *Application) ProxyConfig() api.ProxyOutpostConfig {
	return a.proxyConfig
}

func (a *Application) ServeHTTP(rw http.ResponseWriter, r *http.Request) {
	a.mux.ServeHTTP(rw, r)
}

func (a *Application) Stop() {
	a.authHeaderCache.Stop()
}

func (a *Application) handleSignOut(rw http.ResponseWriter, r *http.Request) {
	redirect := a.endpoint.EndSessionEndpoint
	s, err := a.sessions.Get(r, a.SessionName())
	if err != nil {
		a.redirectToStart(rw, r)
		return
	}
	c, exists := s.Values[constants.SessionClaims]
	if c == nil && !exists {
		a.redirectToStart(rw, r)
		return
	}
	cc := c.(Claims)
	uv := url.Values{
		"id_token_hint": []string{cc.RawToken},
	}
	redirect += "?" + uv.Encode()
	err = a.Logout(cc.Sub)
	if err != nil {
		a.log.WithError(err).Warning("failed to logout of other sessions")
	}
	http.Redirect(rw, r, redirect, http.StatusFound)
}
