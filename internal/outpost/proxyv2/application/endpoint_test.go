package application

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
)

func TestEndpointDefault(t *testing.T) {
	pc := api.ProxyOutpostConfig{
		OidcConfiguration: api.OpenIDConnectConfiguration{
			AuthorizationEndpoint: "https://test.goauthentik.io/application/o/authorize/",
			EndSessionEndpoint:    "https://test.goauthentik.io/application/o/test-app/end-session/",
			IntrospectionEndpoint: "https://test.goauthentik.io/application/o/introspect/",
			Issuer:                "https://test.goauthentik.io/application/o/test-app/",
			JwksUri:               "https://test.goauthentik.io/application/o/test-app/jwks/",
			TokenEndpoint:         "https://test.goauthentik.io/application/o/token/",
		},
	}

	ep := GetOIDCEndpoint(pc, "https://authentik-host.test.goauthentik.io", false)
	// Standard outpost, non embedded
	// All URLs should use the host that they get from the config
	assert.Equal(t, "https://test.goauthentik.io/application/o/authorize/", ep.AuthURL)
	assert.Equal(t, "https://test.goauthentik.io/application/o/token/", ep.TokenURL)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/", ep.Issuer)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/jwks/", ep.JwksUri)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/end-session/", ep.EndSessionEndpoint)
	assert.Equal(t, "https://test.goauthentik.io/application/o/introspect/", ep.TokenIntrospection)
}

func TestEndpointAuthentikHostBrowser(t *testing.T) {
	c := config.Get()
	c.AuthentikHostBrowser = "https://browser.test.goauthentik.io"
	defer func() {
		c.AuthentikHostBrowser = ""
	}()
	pc := api.ProxyOutpostConfig{
		OidcConfiguration: api.OpenIDConnectConfiguration{
			AuthorizationEndpoint: "https://test.goauthentik.io/application/o/authorize/",
			EndSessionEndpoint:    "https://test.goauthentik.io/application/o/test-app/end-session/",
			IntrospectionEndpoint: "https://test.goauthentik.io/application/o/introspect/",
			Issuer:                "https://test.goauthentik.io/application/o/test-app/",
			JwksUri:               "https://test.goauthentik.io/application/o/test-app/jwks/",
			TokenEndpoint:         "https://test.goauthentik.io/application/o/token/",
			UserinfoEndpoint:      "https://test.goauthentik.io/application/o/userinfo/",
		},
	}

	ep := GetOIDCEndpoint(pc, "https://authentik-host.test.goauthentik.io", false)
	// Standard outpost, with AUTHENTIK_HOST_BROWSER set
	// Only the authorize/end session URLs should be changed
	assert.Equal(t, "https://browser.test.goauthentik.io/application/o/authorize/", ep.AuthURL)
	assert.Equal(t, "https://browser.test.goauthentik.io/application/o/test-app/end-session/", ep.EndSessionEndpoint)
	assert.Equal(t, "https://test.goauthentik.io/application/o/token/", ep.TokenURL)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/", ep.Issuer)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/jwks/", ep.JwksUri)
	assert.Equal(t, "https://test.goauthentik.io/application/o/introspect/", ep.TokenIntrospection)
}

func TestEndpointEmbedded(t *testing.T) {
	pc := api.ProxyOutpostConfig{
		OidcConfiguration: api.OpenIDConnectConfiguration{
			AuthorizationEndpoint: "https://test.goauthentik.io/application/o/authorize/",
			EndSessionEndpoint:    "https://test.goauthentik.io/application/o/test-app/end-session/",
			IntrospectionEndpoint: "https://test.goauthentik.io/application/o/introspect/",
			Issuer:                "https://test.goauthentik.io/application/o/test-app/",
			JwksUri:               "https://test.goauthentik.io/application/o/test-app/jwks/",
			TokenEndpoint:         "https://test.goauthentik.io/application/o/token/",
			UserinfoEndpoint:      "https://test.goauthentik.io/application/o/userinfo/",
		},
	}

	ep := GetOIDCEndpoint(pc, "https://authentik-host.test.goauthentik.io", true)
	// Embedded outpost
	// Browser URLs should use the config of "authentik_host", everything else can use what's
	// received from the API endpoint
	// Token URL is an exception since it's sent via a special HTTP transport that overrides the
	// HTTP Host header, to make sure it's the same value as the issuer
	assert.Equal(t, "https://authentik-host.test.goauthentik.io/application/o/authorize/", ep.AuthURL)
	assert.Equal(t, "https://authentik-host.test.goauthentik.io/application/o/test-app/", ep.Issuer)
	assert.Equal(t, "https://test.goauthentik.io/application/o/token/", ep.TokenURL)
	assert.Equal(t, "https://test.goauthentik.io/application/o/test-app/jwks/", ep.JwksUri)
	assert.Equal(t, "https://authentik-host.test.goauthentik.io/application/o/test-app/end-session/", ep.EndSessionEndpoint)
	assert.Equal(t, "https://test.goauthentik.io/application/o/introspect/", ep.TokenIntrospection)
}
