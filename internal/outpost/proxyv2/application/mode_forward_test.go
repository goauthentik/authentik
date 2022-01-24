package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/quasoft/memstore"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func newTestApplication() *Application {
	a, _ := NewApplication(
		api.ProxyOutpostConfig{
			Name:          *api.PtrString(ak.TestSecret()),
			ClientId:      api.PtrString(ak.TestSecret()),
			ClientSecret:  api.PtrString(ak.TestSecret()),
			CookieSecret:  api.PtrString(ak.TestSecret()),
			CookieDomain:  api.PtrString(""),
			Mode:          api.PROXYMODE_FORWARD_SINGLE.Ptr(),
			SkipPathRegex: api.PtrString(""),
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

func TestForwardHandleTraefik_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/traefik", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	assert.Equal(t, rr.Code, http.StatusTemporaryRedirect)
	loc, _ := rr.Result().Location()
	assert.Equal(t, loc.String(), "/akprox/start")

	s, _ := a.sessions.Get(req, constants.SeesionName)
	// Since we're not setting the traefik specific headers, expect it to redirect to the auth URL
	assert.Equal(t, s.Values[constants.SessionRedirect], "/akprox/auth/traefik")
}

func TestForwardHandleTraefik_Headers(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/traefik", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/")

	rr := httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	assert.Equal(t, rr.Code, http.StatusTemporaryRedirect)
	loc, _ := rr.Result().Location()
	assert.Equal(t, loc.String(), "http://test.goauthentik.io/akprox/start")

	s, _ := a.sessions.Get(req, constants.SeesionName)
	assert.Equal(t, s.Values[constants.SessionRedirect], "http://test.goauthentik.io/")
}

func TestForwardHandleNginx_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, rr.Code, http.StatusUnauthorized)
}
