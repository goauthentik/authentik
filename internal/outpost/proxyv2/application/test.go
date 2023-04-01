package application

import (
	"net/http"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/ak"
)

type testServer struct {
	api  *ak.APIController
	apps []*Application
}

func newTestServer() *testServer {
	return &testServer{
		api: ak.MockAK(
			api.Outpost{
				Config: map[string]interface{}{
					"authentik_host": ak.TestSecret(),
				},
			},
			ak.MockConfig(),
		),
		apps: make([]*Application, 0),
	}
}

func (ts *testServer) API() *ak.APIController {
	return ts.api
}

func (ts *testServer) CryptoStore() *ak.CryptoStore {
	return nil
}

func (ts *testServer) Apps() []*Application {
	return ts.apps
}

func newTestApplication() *Application {
	ts := newTestServer()
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
			Mode:                       api.PROXYMODE_FORWARD_SINGLE.Ptr(),
			SkipPathRegex:              api.PtrString("/skip.*"),
			BasicAuthEnabled:           api.PtrBool(true),
			BasicAuthUserAttribute:     api.PtrString("username"),
			BasicAuthPasswordAttribute: api.PtrString("password"),
			OidcConfiguration: api.OpenIDConnectConfiguration{
				AuthorizationEndpoint: "http://fake-auth.t.goauthentik.io/auth",
				TokenEndpoint:         "http://fake-auth.t.goauthentik.io/token",
				UserinfoEndpoint:      "http://fake-auth.t.goauthentik.io/userinfo",
			},
		},
		http.DefaultClient,
		ts,
	)
	ts.apps = append(ts.apps, a)
	return a
}
