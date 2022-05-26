package application

import (
	"net/http"

	"github.com/quasoft/memstore"
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
			CookieDomain:               api.PtrString(""),
			Mode:                       *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_SINGLE.Ptr()),
			SkipPathRegex:              api.PtrString("/skip.*"),
			BasicAuthEnabled:           api.PtrBool(true),
			BasicAuthUserAttribute:     api.PtrString("username"),
			BasicAuthPasswordAttribute: api.PtrString("password"),
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
	a.sessions = memstore.NewMemStore(
		[]byte(ak.TestSecret()),
	)
	return a
}
