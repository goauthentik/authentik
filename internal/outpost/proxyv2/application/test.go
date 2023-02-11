package application

import (
	"net/http"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ak"
)

func newTestApplication() *Application {
	a, _ := NewApplication(
		api.ProxyOutpostConfig{
			Name:                       ak.TestSecret(),
			ClientId:                   api.PtrString(ak.TestSecret()),
			ClientSecret:               api.PtrString(ak.TestSecret()),
			CookieSecret:               api.PtrString(ak.TestSecret()),
			ExternalHost:               "https://ext.t.goauthentik.io",
			InternalHost:               api.PtrString("http://backend"),
			InternalHostSslValidation:  api.PtrBool(true),
			CookieDomain:               api.PtrString(""),
			Mode:                       *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_SINGLE.Ptr()),
			SkipPathRegex:              api.PtrString("/skip.*"),
			BasicAuthEnabled:           api.PtrBool(true),
			BasicAuthUserAttribute:     api.PtrString("username"),
			BasicAuthPasswordAttribute: api.PtrString("password"),
			OidcConfiguration: api.ProxyOutpostConfigOidcConfiguration{
				AuthorizationEndpoint: "http://fake-auth.t.goauthentik.io/auth",
				TokenEndpoint:         "http://fake-auth.t.goauthentik.io/token",
				UserinfoEndpoint:      "http://fake-auth.t.goauthentik.io/userinfo",
			},
		},
		http.DefaultClient,
		nil,
		ak.MockAK(
			api.Outpost{
				Config: map[string]interface{}{
					"authentik_host": ak.TestSecret(),
				},
			},
			ak.MockConfig(),
		),
	)
	return a
}
