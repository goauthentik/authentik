package application

import (
	"net/url"
	"os"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/api"
	"golang.org/x/oauth2"
)

type OIDCEndpoint struct {
	oauth2.Endpoint
	EndSessionEndpoint string
}

func GetOIDCEndpoint(p api.ProxyOutpostConfig, authentikHost string) OIDCEndpoint {
	authUrl := p.OidcConfiguration.AuthorizationEndpoint
	endUrl := p.OidcConfiguration.EndSessionEndpoint
	if browserHost, found := os.LookupEnv("AUTHENTIK_HOST_BROWSER"); found && browserHost != "" {
		host := os.Getenv("AUTHENTIK_HOST")
		authUrl = strings.ReplaceAll(authUrl, host, browserHost)
		endUrl = strings.ReplaceAll(endUrl, host, browserHost)
	}
	ep := OIDCEndpoint{
		Endpoint: oauth2.Endpoint{
			AuthURL:   authUrl,
			TokenURL:  p.OidcConfiguration.TokenEndpoint,
			AuthStyle: oauth2.AuthStyleInParams,
		},
		EndSessionEndpoint: endUrl,
	}
	authU, err := url.Parse(authUrl)
	if err != nil {
		return ep
	}
	endU, err := url.Parse(endUrl)
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
	ep.AuthURL = authU.String()
	ep.EndSessionEndpoint = endU.String()
	return ep
}
