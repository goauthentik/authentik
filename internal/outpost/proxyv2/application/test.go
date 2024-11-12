package application

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

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
			CookieDomain:               api.PtrString(""),
			CookieSecret:               api.PtrString(ak.TestSecret()),
			ExternalHost:               "https://ext.t.goauthentik.io",
			InternalHost:               api.PtrString("http://backend"),
			InternalHostSslValidation:  api.PtrBool(true),
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
		nil,
	)
	ts.apps = append(ts.apps, a)
	return a
}

func (a *Application) assertState(t *testing.T, req *http.Request, response *httptest.ResponseRecorder) (*url.URL, *OAuthState) {
	loc, _ := response.Result().Location()
	q := loc.Query()
	state := q.Get("state")
	a.log.WithField("actual", state).Warning("actual state")
	// modify request to set state so we can parse it
	nr := req.Clone(req.Context())
	nrq := nr.URL.Query()
	nrq.Set("state", state)
	nr.URL.RawQuery = nrq.Encode()
	// parse state
	parsed := a.stateFromRequest(nr)
	if parsed == nil {
		panic("Could not parse state")
	}

	// Remove state from URL
	q.Del("state")
	loc.RawQuery = q.Encode()
	return loc, parsed
}
