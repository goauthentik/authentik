package application

import (
	"net/url"

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
	jwksUri := p.OidcConfiguration.JwksUri
	issuer := p.OidcConfiguration.Issuer
	ep := OIDCEndpoint{
		Endpoint: oauth2.Endpoint{
			AuthURL:   authUrl,
			TokenURL:  p.OidcConfiguration.TokenEndpoint,
			AuthStyle: oauth2.AuthStyleInParams,
		},
		EndSessionEndpoint: endUrl,
		JwksUri:            jwksUri,
		TokenIntrospection: p.OidcConfiguration.IntrospectionEndpoint,
		Issuer:             issuer,
	}
	aku, err := url.Parse(authentikHost)
	if err != nil {
		return ep
	}
	// For the embedded outpost, we use the configure `authentik_host` for the browser URLs
	// and localhost (which is what we've got from the API) for backchannel URLs
	//
	// For other outposts, when `AUTHENTIK_HOST_BROWSER` is set, we use that for the browser URLs
	// and use what we got from the API for backchannel
	hostBrowser := config.Get().AuthentikHostBrowser
	if !embedded && hostBrowser == "" {
		return ep
	}
	var newHost *url.URL = aku
	var newBrowserHost *url.URL
	if embedded {
		if authentikHost == "" {
			log.Warning("Outpost has localhost/blank API Connection but no authentik_host is configured.")
			return ep
		}
		newBrowserHost = aku
	} else if hostBrowser != "" {
		browser, err := url.Parse(hostBrowser)
		if err != nil {
			return ep
		}
		newBrowserHost = browser
	}
	// Update all browser-accessed URLs to use the new host and scheme
	ep.AuthURL = updateURL(authUrl, newBrowserHost.Scheme, newBrowserHost.Host)
	ep.EndSessionEndpoint = updateURL(endUrl, newBrowserHost.Scheme, newBrowserHost.Host)
	// Update issuer to use the same host and scheme, which would normally break as we don't
	// change the token URL here, but the token HTTP transport overwrites the Host header
	//
	// This is only used in embedded outposts as there we can guarantee that the request
	// is routed correctly
	if embedded {
		ep.Issuer = updateURL(ep.Issuer, newHost.Scheme, newHost.Host)
		ep.JwksUri = updateURL(jwksUri, newHost.Scheme, newHost.Host)
	}
	return ep
}
