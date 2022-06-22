package application

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func TestRedirectToStart_Proxy(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_PROXY.Ptr())
	a.proxyConfig.ExternalHost = "https://test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/foo/bar/baz", nil)

	rr := httptest.NewRecorder()
	a.redirectToStart(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "https://test.goauthentik.io/outpost.goauthentik.io/start?rd=https%3A%2F%2Ftest.goauthentik.io%2Ffoo%2Fbar%2Fbaz", loc.String())

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "https://test.goauthentik.io/foo/bar/baz", s.Values[constants.SessionRedirect])
}

func TestRedirectToStart_Forward(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_SINGLE.Ptr())
	a.proxyConfig.ExternalHost = "https://test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/foo/bar/baz", nil)

	rr := httptest.NewRecorder()
	a.redirectToStart(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "https://test.goauthentik.io/outpost.goauthentik.io/start?rd=https%3A%2F%2Ftest.goauthentik.io%2Ffoo%2Fbar%2Fbaz", loc.String())

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "https://test.goauthentik.io/foo/bar/baz", s.Values[constants.SessionRedirect])
}

func TestRedirectToStart_Forward_Domain_Invalid(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_DOMAIN.Ptr())
	a.proxyConfig.ExternalHost = "https://test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/foo/bar/baz", nil)

	rr := httptest.NewRecorder()
	a.redirectToStart(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "https://test.goauthentik.io/outpost.goauthentik.io/start?rd=https%3A%2F%2Ftest.goauthentik.io", loc.String())

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "https://test.goauthentik.io", s.Values[constants.SessionRedirect])
}

func TestRedirectToStart_Forward_Domain(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.CookieDomain = api.PtrString("goauthentik.io")
	a.proxyConfig.Mode = *api.NewNullableProxyMode(api.PROXYMODE_FORWARD_DOMAIN.Ptr())
	a.proxyConfig.ExternalHost = "https://test.goauthentik.io"
	req, _ := http.NewRequest("GET", "/foo/bar/baz", nil)

	rr := httptest.NewRecorder()
	a.redirectToStart(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(t, "https://test.goauthentik.io/outpost.goauthentik.io/start?rd=https%3A%2F%2Ftest.goauthentik.io", loc.String())

	s, _ := a.sessions.Get(req, constants.SessionName)
	assert.Equal(t, "https://test.goauthentik.io", s.Values[constants.SessionRedirect])
}
