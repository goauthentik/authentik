package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func TestForwardHandleCaddy_Single_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)
}

func TestForwardHandleCaddy_Single_Skip(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/skip")

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

func TestForwardHandleCaddy_Single_Headers(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/app")

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	assert.Equal(t, rr.Code, http.StatusTemporaryRedirect)
	loc, _ := rr.Result().Location()
	assert.Equal(t, loc.String(), "http://test.goauthentik.io/outpost.goauthentik.io/start")

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}

func TestForwardHandleCaddy_Single_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/app")

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	s, _ := a.sessions.Get(req, constants.SessionName)
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
		Proxy: &ProxyClaims{
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
	a.forwardHandleCaddy(rr, req)

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

func TestForwardHandleCaddy_Domain_Blank(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_DOMAIN.Ptr())
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)
}

func TestForwardHandleCaddy_Domain_Header(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_DOMAIN.Ptr())
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	a.proxyConfig.ExternalHost = "http://auth.test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/caddy", nil)
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Forwarded-Host", "test.goauthentik.io")
	req.Header.Set("X-Forwarded-Uri", "/app")

	rr := httptest.NewRecorder()
	a.forwardHandleCaddy(rr, req)

	assert.Equal(t, http.StatusTemporaryRedirect, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "http://auth.test.goauthentik.io/outpost.goauthentik.io/start", loc.String())

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}
