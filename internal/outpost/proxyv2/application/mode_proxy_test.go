package application

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func TestProxy_ModifyRequest(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http://frontend/foo", nil)
	u, err := url.Parse("http://backend:8012")
	if err != nil {
		panic(err)
	}
	a.proxyModifyRequest(u)(req)

	assert.Equal(t, "frontend", req.Header.Get("X-Forwarded-Host"))
	assert.Equal(t, "/foo", req.URL.Path)
	assert.Equal(t, "backend:8012", req.URL.Host)
	assert.Equal(t, "frontend", req.Host)
}

func TestProxy_ModifyRequest_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http://frontend/foo", nil)
	u, err := url.Parse("http://backend:8012")
	if err != nil {
		panic(err)
	}
	rr := httptest.NewRecorder()

	s, _ := a.sessions.Get(req, constants.SessionName)
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
		Proxy: &ProxyClaims{
			BackendOverride: "http://other-backend:8123",
		},
	}
	err = a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	a.proxyModifyRequest(u)(req)

	assert.Equal(t, "/foo", req.URL.Path)
	assert.Equal(t, "other-backend:8123", req.URL.Host)
	assert.Equal(t, "frontend", req.Host)
}

func TestProxy_ModifyRequest_Claims_Invalid(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http://frontend/foo", nil)
	u, err := url.Parse("http://backend:8012")
	if err != nil {
		panic(err)
	}
	rr := httptest.NewRecorder()

	s, _ := a.sessions.Get(req, constants.SessionName)
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
		Proxy: &ProxyClaims{
			BackendOverride: ":qewr",
		},
	}
	err = a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	a.proxyModifyRequest(u)(req)

	assert.Equal(t, "/foo", req.URL.Path)
	assert.Equal(t, "backend:8012", req.URL.Host)
	assert.Equal(t, "frontend", req.Host)
}
