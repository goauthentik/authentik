package application

import (
	"net/url"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"golang.org/x/oauth2"
)

type OIDCEndpoint struct {
	oauth2.Endpoint
	TokenIntrospection string
	EndSessionEndpoint string
	JwksUri            string
	Issuer             string
}

func updateURL(rawUrl string, scheme string, host string) string {
	u, err := url.Parse(rawUrl)
	if err != nil {
		return rawUrl
	}
	u.Host = host
	u.Scheme = scheme
	return u.String()
}

func GetOIDCEndpoint(p api.ProxyOutpostConfig, authentikHost string, embedded bool) OIDCEndpoint {
	authUrl := p.OidcConfiguration.AuthorizationEndpoint
	endUrl := p.OidcConfiguration.EndSessionEndpoint
	tokenUrl := p.OidcConfiguration.TokenEndpoint
	jwksUrl := p.OidcConfiguration.JwksUri
	issuer := p.OidcConfiguration.Issuer
	if config.Get().AuthentikHostBrowser != "" {
		authUrl = strings.ReplaceAll(authUrl, authentikHost, config.Get().AuthentikHostBrowser)
		endUrl = strings.ReplaceAll(endUrl, authentikHost, config.Get().AuthentikHostBrowser)
		jwksUrl = strings.ReplaceAll(jwksUrl, authentikHost, config.Get().AuthentikHostBrowser)
		issuer = strings.ReplaceAll(issuer, authentikHost, config.Get().AuthentikHostBrowser)
	}
	ep := OIDCEndpoint{
		Endpoint: oauth2.Endpoint{
			AuthURL:   authUrl,
			TokenURL:  tokenUrl,
			AuthStyle: oauth2.AuthStyleInParams,
		},
		EndSessionEndpoint: endUrl,
		JwksUri:            jwksUrl,
		TokenIntrospection: p.OidcConfiguration.IntrospectionEndpoint,
		Issuer:             issuer,
	}
	if !embedded {
		return ep
	}
	if authentikHost == "" {
		log.Warning("Outpost has localhost/blank API Connection but no authentik_host is configured.")
		return ep
	}
	aku, err := url.Parse(authentikHost)
	if err != nil {
		return ep
	}
	ep.AuthURL = updateURL(authUrl, aku.Scheme, aku.Host)
	ep.EndSessionEndpoint = updateURL(endUrl, aku.Scheme, aku.Host)
	ep.JwksUri = updateURL(jwksUrl, aku.Scheme, aku.Host)
	ep.Issuer = updateURL(ep.Issuer, aku.Scheme, aku.Host)
	return ep
}
