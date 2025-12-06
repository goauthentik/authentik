package application

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func TestLogout(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	rr := httptest.NewRecorder()

	// Login once
	s, _ := a.sessions.Get(req, a.SessionName())
	s.ID = uuid.New().String()
	s.Options.MaxAge = 86400
	s.Values[constants.SessionClaims] = types.Claims{
		Sub: "foo",
	}
	err := a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	a.mux.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusBadGateway, rr.Code)

	// Login twice
	s2, _ := a.sessions.Get(req, a.SessionName())
	s2.ID = uuid.New().String()
	s2.Options.MaxAge = 86400
	s2.Values[constants.SessionClaims] = types.Claims{
		Sub: "foo",
	}
	err = a.sessions.Save(req, rr, s2)
	if err != nil {
		panic(err)
	}

	a.mux.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusBadGateway, rr.Code)

	// Logout
	req, _ = http.NewRequest("GET", "https://ext.t.goauthentik.io/outpost.goauthentik.io/sign_out", nil)
	s3, _ := a.sessions.Get(req, a.SessionName())
	s3.ID = uuid.New().String()
	s3.Options.MaxAge = 86400
	s3.Values[constants.SessionClaims] = types.Claims{
		Sub: "foo",
	}
	err = a.sessions.Save(req, rr, s3)
	if err != nil {
		panic(err)
	}

	rr = httptest.NewRecorder()
	a.handleSignOut(rr, req)
	assert.Equal(t, http.StatusFound, rr.Code)

	s1Name := filepath.Join(os.TempDir(), "session_"+s.ID)
	_, err = os.Stat(s1Name)
	assert.True(t, errors.Is(err, os.ErrNotExist))
	s2Name := filepath.Join(os.TempDir(), "session_"+s2.ID)
	_, err = os.Stat(s2Name)
	assert.True(t, errors.Is(err, os.ErrNotExist))
}

func TestStaleCookieDeletion(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()

	// Create a request with a session cookie that references a non-existent session file
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)

	// Set a cookie for a session that doesn't exist (simulates pod restart)
	nonExistentSessionID := uuid.New().String()
	req.AddCookie(&http.Cookie{
		Name:  a.SessionName(),
		Value: "encoded_session_data_" + nonExistentSessionID,
		Path:  "/",
	})

	rr := httptest.NewRecorder()

	// Call getClaimsFromSession which should delete the stale cookie
	claims := a.getClaimsFromSession(rr, req)

	// Verify no claims were returned (session doesn't exist)
	assert.Nil(t, claims)

	// Verify the response includes a Set-Cookie header to delete the stale cookie
	cookies := rr.Result().Cookies()
	var foundDeleteCookie bool
	for _, cookie := range cookies {
		if cookie.Name == a.SessionName() && cookie.MaxAge < 0 {
			foundDeleteCookie = true
			break
		}
	}
	assert.True(t, foundDeleteCookie, "Expected stale session cookie to be deleted")
}

func TestStateFromRequestDeletesStaleCookie(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()

	// Create a valid state JWT (from createState)
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	rr := httptest.NewRecorder()

	state, err := a.createState(req, rr, "/redirect")
	assert.NoError(t, err)

	// Create a new request with the state but a stale session cookie
	req2, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/callback?state="+state, nil)

	// Add a cookie for a non-existent session
	nonExistentSessionID := uuid.New().String()
	req2.AddCookie(&http.Cookie{
		Name:  a.SessionName(),
		Value: "encoded_session_data_" + nonExistentSessionID,
		Path:  "/",
	})

	rr2 := httptest.NewRecorder()

	// Call stateFromRequest which should fail due to missing session
	// but should also delete the stale cookie
	claims := a.stateFromRequest(rr2, req2)

	// Verify no claims were returned
	assert.Nil(t, claims)

	// Verify the response includes a Set-Cookie header to delete the stale cookie
	cookies := rr2.Result().Cookies()
	var foundDeleteCookie bool
	for _, cookie := range cookies {
		if cookie.Name == a.SessionName() && cookie.MaxAge < 0 {
			foundDeleteCookie = true
			break
		}
	}
	assert.True(t, foundDeleteCookie, "Expected stale session cookie to be deleted")
}
