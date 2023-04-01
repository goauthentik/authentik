package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func TestForwardHandleNginx_Single_Blank(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)
}

func TestForwardHandleNginx_Single_Skip(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URL", "http://test.goauthentik.io/skip")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

func TestForwardHandleNginx_Single_Headers(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URL", "http://test.goauthentik.io/app")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusUnauthorized, rr.Code)

	s, _ := a.sessions.Get(req, a.SessionName())
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}

func TestForwardHandleNginx_Single_URI(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "https://foo.bar/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URI", "/app")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusUnauthorized, rr.Code)

	s, _ := a.sessions.Get(req, a.SessionName())
	assert.Equal(t, "/app", s.Values[constants.SessionRedirect])
}

func TestForwardHandleNginx_Single_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URI", "/")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	s, _ := a.sessions.Get(req, a.SessionName())
	s.ID = uuid.New().String()
	s.Options.MaxAge = 86400
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
	a.forwardHandleNginx(rr, req)

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

func TestForwardHandleNginx_Domain_Blank(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)
}

func TestForwardHandleNginx_Domain_Header(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	a.proxyConfig.ExternalHost = "http://auth.test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URL", "http://test.goauthentik.io/app")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusUnauthorized, rr.Code)

	s, _ := a.sessions.Get(req, a.SessionName())
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}
