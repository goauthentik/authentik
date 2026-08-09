package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	api "goauthentik.io/packages/client-go"
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

func TestForwardHandleNginx_Domain_Blank(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = new("foo")
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)
}

func TestForwardHandleNginx_Domain_Header(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = new("foo")
	a.proxyConfig.ExternalHost = "http://auth.test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/nginx", nil)
	req.Header.Set("X-Original-URL", "http://test.goauthentik.io/app")

	rr := httptest.NewRecorder()
	a.forwardHandleNginx(rr, req)

	assert.Equal(t, http.StatusUnauthorized, rr.Code)

	s, _ := a.sessions.Get(req, a.SessionName())
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}
