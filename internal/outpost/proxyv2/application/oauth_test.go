package application

import (
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"
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

	req, _ = http.NewRequest("GET", "/outpost.goauthentik.io/auth/start?rd=https://ext.t.goauthentik.io/test", nil)

	rd, ok = a.checkRedirectParam(req)

	assert.Equal(t, true, ok)
	assert.Equal(t, "https://ext.t.goauthentik.io/test", rd)
}
