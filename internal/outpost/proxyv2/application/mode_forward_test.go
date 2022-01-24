package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/quasoft/memstore"
	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func newTestApplication() *Application {
	a, _ := NewApplication(
		api.ProxyOutpostConfig{
			Name:                       ak.TestSecret(),
			ClientId:                   api.PtrString(ak.TestSecret()),
			ClientSecret:               api.PtrString(ak.TestSecret()),
			CookieSecret:               api.PtrString(ak.TestSecret()),
			CookieDomain:               api.PtrString(""),
			Mode:                       api.PROXYMODE_FORWARD_SINGLE.Ptr(),
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

func TestForwardHandleTraefik_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/traefik", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	assert.Equal(t, http.StatusTemporaryRedirect, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "/akprox/start", loc.String())

	s, _ := a.sessions.Get(req, constants.SeesionName)
	// Since we're not setting the traefik specific headers, expect it to redirect to the auth URL
	assert.Equal(t, "/akprox/auth/traefik", s.Values[constants.SessionRedirect])
}

func TestForwardHandleTraefik_Skip(t *testing.T) {
	logrus.SetLevel(logrus.TraceLevel)
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/traefik", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/skip")

	rr := httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
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
	assert.Equal(t, "http://test.goauthentik.io/", s.Values[constants.SessionRedirect])
}

func TestForwardHandleTraefik_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/traefik", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	s, _ := a.sessions.Get(req, constants.SeesionName)
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
		Proxy: ProxyClaims{
			UserAttributes: map[string]interface{}{
				"username": "foo",
				"password": "bar",
				"additionalHeaders": map[string]interface{}{
					"foo": "bar",
				},
			},
		},
	}
	err := a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	rr = httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	h := rr.Result().Header

	assert.Equal(t, []string{"Basic Zm9vOmJhcg=="}, h["Authorization"])
	assert.Equal(t, []string{"bar"}, h["Foo"])
	assert.Equal(t, []string{""}, h["User-Agent"])
	assert.Equal(t, []string{""}, h["X-Authentik-Email"])
	assert.Equal(t, []string{""}, h["X-Authentik-Groups"])
	assert.Equal(t, []string{""}, h["X-Authentik-Jwt"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-App"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-Jwks"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-Outpost"])
	assert.Equal(t, []string{""}, h["X-Authentik-Name"])
	assert.Equal(t, []string{"foo"}, h["X-Authentik-Uid"])
	assert.Equal(t, []string{""}, h["X-Authentik-Username"])
}

func TestForwardHandleNginx_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusUnauthorized, rr.Code)
}

func TestForwardHandleNginx_Skip(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/nginx", nil)
	req.Header.Set("X-Original-URI", "http://test.goauthentik.io/skip")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

func TestForwardHandleNginx_Headers(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/nginx", nil)
	req.Header.Set("X-Original-URI", "http://test.goauthentik.io")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, rr.Code, http.StatusUnauthorized)

	s, _ := a.sessions.Get(req, constants.SeesionName)
	assert.Equal(t, "http://test.goauthentik.io", s.Values[constants.SessionRedirect])
}

func TestForwardHandleNginx_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/akprox/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	s, _ := a.sessions.Get(req, constants.SeesionName)
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
		Proxy: ProxyClaims{
			UserAttributes: map[string]interface{}{
				"username": "foo",
				"password": "bar",
				"additionalHeaders": map[string]interface{}{
					"foo": "bar",
				},
			},
		},
	}
	err := a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	rr = httptest.NewRecorder()
	a.forwardHandleTraefik(rr, req)

	h := rr.Result().Header

	assert.Equal(t, []string{"Basic Zm9vOmJhcg=="}, h["Authorization"])
	assert.Equal(t, []string{"bar"}, h["Foo"])
	assert.Equal(t, []string{""}, h["User-Agent"])
	assert.Equal(t, []string{""}, h["X-Authentik-Email"])
	assert.Equal(t, []string{""}, h["X-Authentik-Groups"])
	assert.Equal(t, []string{""}, h["X-Authentik-Jwt"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-App"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-Jwks"])
	assert.Equal(t, []string{""}, h["X-Authentik-Meta-Outpost"])
	assert.Equal(t, []string{""}, h["X-Authentik-Name"])
	assert.Equal(t, []string{"foo"}, h["X-Authentik-Uid"])
	assert.Equal(t, []string{""}, h["X-Authentik-Username"])
}
