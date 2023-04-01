package application

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
)

func TestForwardHandleEnvoy_Single_Skip(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http://test.goauthentik.io/skip", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleEnvoy(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

func TestForwardHandleEnvoy_Single_Headers(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http:///app", nil)
	req.Host = "ext.t.goauthentik.io"

	rr := httptest.NewRecorder()
	a.forwardHandleEnvoy(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	s, _ := a.sessions.Get(req, a.SessionName())
	shouldUrl := url.Values{
		"client_id":     []string{*a.proxyConfig.ClientId},
		"redirect_uri":  []string{"https://ext.t.goauthentik.io/outpost.goauthentik.io/callback?X-authentik-auth-callback=true"},
		"response_type": []string{"code"},
		"state":         []string{s.Values[constants.SessionOAuthState].(string)},
	}
	assert.Equal(t, fmt.Sprintf("http://fake-auth.t.goauthentik.io/auth?%s", shouldUrl.Encode()), loc.String())
	assert.Equal(t, "http://ext.t.goauthentik.io/app", s.Values[constants.SessionRedirect])
}

func TestForwardHandleEnvoy_Single_Claims(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "http://test.goauthentik.io/app", nil)

	rr := httptest.NewRecorder()
	a.forwardHandleEnvoy(rr, req)

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
	a.forwardHandleEnvoy(rr, req)

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

func TestForwardHandleEnvoy_Domain_Header(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = api.PtrString("foo")
	a.proxyConfig.ExternalHost = "http://auth.test.goauthentik.io"
	req, _ := http.NewRequest("GET", "http:///app", nil)
	req.Host = "test.goauthentik.io"

	rr := httptest.NewRecorder()
	a.forwardHandleEnvoy(rr, req)

	assert.Equal(t, http.StatusFound, rr.Code)
	loc, _ := rr.Result().Location()
	s, _ := a.sessions.Get(req, a.SessionName())

	shouldUrl := url.Values{
		"client_id":     []string{*a.proxyConfig.ClientId},
		"redirect_uri":  []string{"https://ext.t.goauthentik.io/outpost.goauthentik.io/callback?X-authentik-auth-callback=true"},
		"response_type": []string{"code"},
		"state":         []string{s.Values[constants.SessionOAuthState].(string)},
	}
	assert.Equal(t, fmt.Sprintf("http://fake-auth.t.goauthentik.io/auth?%s", shouldUrl.Encode()), loc.String())
	assert.Equal(t, "http://test.goauthentik.io/app", s.Values[constants.SessionRedirect])
}
