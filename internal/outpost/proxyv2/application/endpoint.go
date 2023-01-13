package application

import (
	"net/url"
	"os"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api/v3"
	"golang.org/x/oauth2"
)

type OIDCEndpoint struct {
	oauth2.Endpoint
	TokenIntrospection string
	EndSessionEndpoint string
	JwksUri            string
}

func GetOIDCEndpoint(p api.ProxyOutpostConfig, authentikHost string) OIDCEndpoint {
	authUrl := p.OidcConfiguration.AuthorizationEndpoint
	endUrl := p.OidcConfiguration.EndSessionEndpoint
	jwksUrl := p.OidcConfiguration.JwksUri
	if browserHost, found := os.LookupEnv("AUTHENTIK_HOST_BROWSER"); found && browserHost != "" {
		host := os.Getenv("AUTHENTIK_HOST")
		authUrl = strings.ReplaceAll(authUrl, host, browserHost)
		endUrl = strings.ReplaceAll(endUrl, host, browserHost)
		jwksUrl = strings.ReplaceAll(jwksUrl, host, browserHost)
	}
	ep := OIDCEndpoint{
		Endpoint: oauth2.Endpoint{
			AuthURL:   authUrl,
			TokenURL:  p.OidcConfiguration.TokenEndpoint,
			AuthStyle: oauth2.AuthStyleInParams,
		},
		EndSessionEndpoint: endUrl,
		JwksUri:            jwksUrl,
	}
	authU, err := url.Parse(authUrl)
	if err != nil {
		return ep
	}
	endU, err := url.Parse(endUrl)
	if err != nil {
		return ep
	}
	jwksU, err := url.Parse(jwksUrl)
	if err != nil {
		return ep
	}
	if authU.Host != "localhost:8000" {
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
	authU.Host = aku.Host
	authU.Scheme = aku.Scheme
	endU.Host = aku.Host
	endU.Scheme = aku.Scheme
	jwksU.Host = aku.Host
	jwksU.Scheme = aku.Scheme
	ep.AuthURL = authU.String()
	ep.EndSessionEndpoint = endU.String()
	ep.JwksUri = jwksU.String()
	ep.TokenIntrospection = p.OidcConfiguration.IntrospectionEndpoint
	return ep
}
