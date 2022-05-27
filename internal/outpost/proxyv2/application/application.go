package application

import (
	"context"
	"crypto/tls"
	"encoding/gob"
	"fmt"
	"html/template"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

	"github.com/coreos/go-oidc"
	"github.com/getsentry/sentry-go"
	sentryhttp "github.com/getsentry/sentry-go/http"
	"github.com/gorilla/mux"
	"github.com/gorilla/sessions"
	"github.com/pkg/errors"
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

	endpint       OIDCEndpoint
	oauthConfig   oauth2.Config
	tokenVerifier *oidc.IDTokenVerifier
	outpostName   string

	sessions    sessions.Store
	proxyConfig api.ProxyOutpostConfig
	httpClient  *http.Client

	log *log.Entry
	mux *mux.Router
	ak  *ak.APIController

	errorTemplates *template.Template
}

func NewApplication(p api.ProxyOutpostConfig, c *http.Client, cs *ak.CryptoStore, ak *ak.APIController) (*Application, error) {
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

	var verifier = oidc.NewVerifier(p.OidcConfiguration.Issuer, ks, &oidc.Config{
		ClientID:             *p.ClientId,
		SupportedSigningAlgs: []string{"RS256", "HS256"},
	})

	// Configure an OpenID Connect aware OAuth2 client.
	endpoint := GetOIDCEndpoint(p, ak.Outpost.Config["authentik_host"].(string))
	oauth2Config := oauth2.Config{
		ClientID:     *p.ClientId,
		ClientSecret: *p.ClientSecret,
		RedirectURL:  urlJoin(p.ExternalHost, "/outpost.goauthentik.io/callback"),
		Endpoint:     endpoint.Endpoint,
		Scopes:       p.ScopesToRequest,
	}
	mux := mux.NewRouter()
	a := &Application{
		Host:           externalHost.Host,
		log:            muxLogger,
		outpostName:    ak.Outpost.Name,
		endpint:        endpoint,
		oauthConfig:    oauth2Config,
		tokenVerifier:  verifier,
		proxyConfig:    p,
		httpClient:     c,
		mux:            mux,
		errorTemplates: templates.GetTemplates(),
		ak:             ak,
	}
	a.sessions = a.getStore(p, externalHost)
	mux.Use(web.NewLoggingHandler(muxLogger, func(l *log.Entry, r *http.Request) *log.Entry {
		s, err := a.sessions.Get(r, constants.SessionName)
		if err != nil {
			return l
		}
		claims, ok := s.Values[constants.SessionClaims]
		if claims == nil || !ok {
			return l
		}
		c, ok := claims.(Claims)
		if !ok {
			return l
		}
		return l.WithField("request_username", c.PreferredUsername)
	}))
	mux.Use(func(inner http.Handler) http.Handler {
		return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
			c, _ := a.getClaims(r)
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
	mux.Use(sentryhttp.New(sentryhttp.Options{}).Handle)

	// Support /start and /sign_in for backwards compatibility
	mux.HandleFunc("/outpost.goauthentik.io/start", a.handleRedirect)
	mux.HandleFunc("/outpost.goauthentik.io/sign_in", a.handleRedirect)
	mux.HandleFunc("/outpost.goauthentik.io/callback", a.handleCallback)
	mux.HandleFunc("/outpost.goauthentik.io/sign_out", a.handleSignOut)
	switch *p.Mode.Get() {
	case api.PROXYMODE_PROXY:
		err = a.configureProxy()
	case api.PROXYMODE_FORWARD_SINGLE:
		fallthrough
	case api.PROXYMODE_FORWARD_DOMAIN:
		err = a.configureForward()
	}
	if err != nil {
		return nil, errors.Wrap(err, "failed to configure application mode")
	}

	if kp := p.Certificate.Get(); kp != nil {
		err := cs.AddKeypair(*kp)
		if err != nil {
			return nil, errors.Wrap(err, "failed to initially fetch certificate")
		}
		a.Cert = cs.Get(*kp)
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
	return *a.proxyConfig.Mode.Get()
}

func (a *Application) ProxyConfig() api.ProxyOutpostConfig {
	return a.proxyConfig
}

func (a *Application) ServeHTTP(rw http.ResponseWriter, r *http.Request) {
	a.mux.ServeHTTP(rw, r)
}

func (a *Application) handleSignOut(rw http.ResponseWriter, r *http.Request) {
	//TODO: Token revocation
	s, err := a.sessions.Get(r, constants.SessionName)
	if err != nil {
		http.Redirect(rw, r, a.endpint.EndSessionEndpoint, http.StatusFound)
		return
	}
	s.Options.MaxAge = -1
	err = s.Save(r, rw)
	if err != nil {
		http.Redirect(rw, r, a.endpint.EndSessionEndpoint, http.StatusFound)
		return
	}
	http.Redirect(rw, r, a.endpint.EndSessionEndpoint, http.StatusFound)
}
