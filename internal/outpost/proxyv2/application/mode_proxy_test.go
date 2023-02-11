package application

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/google/uuid"
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

func TestProxy_Redirect(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	rr := httptest.NewRecorder()

	a.mux.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(
		t,
		"https://ext.t.goauthentik.io/outpost.goauthentik.io/start?rd=https%3A%2F%2Fext.t.goauthentik.io%2Ffoo",
		loc.String(),
	)
}

func TestProxy_Redirect_Subdirectory(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.ExternalHost = a.proxyConfig.ExternalHost + "/subdir"
	_ = a.configureProxy()
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	rr := httptest.NewRecorder()

	a.mux.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	assert.Equal(
		t,
		"https://ext.t.goauthentik.io/subdir/outpost.goauthentik.io/start?rd=https%3A%2F%2Fext.t.goauthentik.io%2Ffoo",
		loc.String(),
	)
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
	s.ID = uuid.New().String()
	s.Options.MaxAge = 86400
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
	s.ID = uuid.New().String()
	s.Options.MaxAge = 86400
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
