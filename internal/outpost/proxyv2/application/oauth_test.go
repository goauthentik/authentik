package application

import (
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

func TestCheckRedirectParam(t *testing.T) {
	a := newTestApplication()
	req, _ := http.NewRequest("GET", "/outpost.goauthentik.io/auth/start", nil)

	rd, ok := a.checkRedirectParam(req)

	assert.Equal(t, false, ok)
	assert.Equal(t, "", rd)

	req, _ = http.NewRequest("GET", "/outpost.goauthentik.io/auth/start?rd=https://google.com", nil)

	rd, ok = a.checkRedirectParam(req)

	assert.Equal(t, false, ok)
	assert.Equal(t, "", rd)

	req, _ = http.NewRequest("GET", "/outpost.goauthentik.io/auth/start?rd=https://ext.t.goauthentik.io/test?foo", nil)

	rd, ok = a.checkRedirectParam(req)

	assert.Equal(t, true, ok)
	assert.Equal(t, "https://ext.t.goauthentik.io/test?foo", rd)
}

func TestCheckRedirectParam_Domain(t *testing.T) {
	a := newTestApplication()
	a.proxyConfig.Mode = api.PROXYMODE_FORWARD_DOMAIN.Ptr()
	a.proxyConfig.CookieDomain = api.PtrString("t.goauthentik.io")
	req, _ := http.NewRequest("GET", "https://a.t.goauthentik.io/outpost.goauthentik.io/auth/start", nil)

	rd, ok := a.checkRedirectParam(req)

	assert.Equal(t, false, ok)
	assert.Equal(t, "", rd)
	req, _ = http.NewRequest("GET", "/outpost.goauthentik.io/auth/start?rd=https://ext.t.goauthentik.io/test", nil)

	rd, ok = a.checkRedirectParam(req)

	assert.Equal(t, true, ok)
	assert.Equal(t, "https://ext.t.goauthentik.io/test", rd)
}
