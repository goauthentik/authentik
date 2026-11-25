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

// Only the outpost's own endpoints are reachable without a session. A forwarded
// path that merely resembles one must still be authenticated.
func TestForwardHandleNginx_Single_NonEndpointPrefix(t *testing.T) {
	paths := []string{
		"/outpost.goauthentik.io/../private",
		"/outpost.goauthentik.io/%2e%2e/private",
		"/outpost.goauthentik.io//../private",
		"/outpost.goauthentik.io/%2f../private",
		"/outpost.goauthentik.io/%2F../private",
		"/outpost.goauthentik.io%2f..%2fprivate",
		"/outpost.goauthentik.io/..%2fprivate",
		"/outpost.goauthentik.io%2F%2e%2e%2Fprivate",
		"/outpost.goauthentik.io%2fanything%2f..%2f..%2fprivate",
		"/%6futpost.goauthentik.io/..%2fprivate",
		"/outpost.goauthentik.io-spa/admin",
		"/outpost.goauthentik.ioANYTHING",
		"/outpost.goauthentik.io/static/../../private",
		"/outpost.goauthentik.io/auth/envoy/../../private",
	}
	for _, p := range paths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusUnauthorized, rr.Code)
		})
	}
}

// The outpost's own endpoints stay reachable without a session.
func TestForwardHandleNginx_Single_Endpoints(t *testing.T) {
	paths := []string{
		"/outpost.goauthentik.io/start",
		"/outpost.goauthentik.io/callback",
		"/outpost.goauthentik.io/sign_out",
		"/outpost.goauthentik.io/ping",
		"/outpost.goauthentik.io/auth/nginx",
		"/outpost.goauthentik.io/auth/traefik",
		"/outpost.goauthentik.io/auth/caddy",
		"/outpost.goauthentik.io/auth/envoy",
	}
	for _, p := range paths {
		t.Run(p, func(t *testing.T) {
			a := newTestApplication()
			req, _ := http.NewRequest("GET", nginxPrefix, nil)
			req.Header.Set("X-Original-URL", "http://test.goauthentik.io"+p)

			rr := httptest.NewRecorder()
			a.forwardHandleNginx(rr, req)

			assert.Equal(t, http.StatusOK, rr.Code)
		})
	}
}
