package application

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/mitchellh/mapstructure"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/filesystemstore"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func sessionPath(id string) string {
	return filepath.Join(os.TempDir(), "session_"+id)
}

// withStoreMaxAge gives the session store a real lifetime for the duration of a
// test. newTestApplication builds a provider without AccessTokenValidity, which
// leaves the store's MaxAge at 0 — and a store whose MaxAge is <= 0 erases on
// every Save() instead of persisting, so no session ever round-trips.
func withStoreMaxAge(t *testing.T, a *Application, maxAge int) {
	t.Helper()
	store, ok := a.sessions.(*filesystemstore.Store)
	if !ok {
		t.Fatalf("expected a filesystem store, got %T", a.sessions)
	}
	previous := store.Options.MaxAge
	store.Options.MaxAge = maxAge
	t.Cleanup(func() { store.Options.MaxAge = previous })
}

// lastSessionCookie returns the final Set-Cookie carrying the session name.
// A response may set it more than once; clients apply them in order, so the
// last one is what actually ends up in the cookie jar.
func lastSessionCookie(t *testing.T, a *Application, rr *httptest.ResponseRecorder) *http.Cookie {
	t.Helper()
	var found *http.Cookie
	for _, cookie := range rr.Result().Cookies() {
		if cookie.Name == a.SessionName() {
			found = cookie
		}
	}
	if found == nil {
		t.Fatal("no session cookie was set")
	}
	return found
}

// parseState decodes a state JWT without checking it against a session, so
// tests can inspect the session ID it references.
func parseState(t *testing.T, a *Application, state string) *OAuthState {
	t.Helper()
	token, err := jwt.Parse(state, func(token *jwt.Token) (any, error) {
		return []byte(a.proxyConfig.GetCookieSecret()), nil
	})
	assert.NoError(t, err)
	claims := &OAuthState{}
	assert.NoError(t, mapstructure.Decode(token.Claims, claims))
	return claims
}

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

func TestCreateStateWithStaleCookie(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()
	withStoreMaxAge(t, a, 86400)

	// Create a request with a stale session cookie (simulates outpost restart or user change)
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/outpost.goauthentik.io/start", nil)

	// Add a cookie for a non-existent session
	nonExistentSessionID := uuid.New().String()
	req.AddCookie(&http.Cookie{
		Name:  a.SessionName(),
		Value: "encoded_session_data_" + nonExistentSessionID,
		Path:  "/",
	})

	rr := httptest.NewRecorder()

	// Call createState which should succeed despite the stale cookie
	state, err := a.createState(req, rr, "/redirect")

	// Verify createState succeeded
	assert.NoError(t, err)
	assert.NotEmpty(t, state)

	// The state must reference a session that was actually written to the store,
	// otherwise the callback rejects it with "mismatched session ID".
	parsed := parseState(t, a, state)
	assert.NotEqual(t, nonExistentSessionID, parsed.SessionID)
	assert.FileExists(t, sessionPath(parsed.SessionID))

	// The client has to be left holding that session, so the cookie must be a
	// persisting one rather than a deletion.
	cookie := lastSessionCookie(t, a, rr)
	assert.Greater(t, cookie.MaxAge, 0, "Expected a persisting session cookie, not a deletion")
}

// TestCreateStateAfterSignOut reproduces the forward-auth sequence that runs
// after signing out: the session file is gone but the client still presents its
// cookie, so checkAuth fails and hands off to the auth start.
//
// Both halves run inside one request and therefore share a single gorilla
// session registry, which memoises the *sessions.Session — Options included.
// Expiring the stale cookie by setting MaxAge = -1 on that shared object used to
// leak into createState's Save(), which then erased the new session instead of
// persisting it and minted a state JWT for a session that existed nowhere.
func TestCreateStateAfterSignOut(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()
	withStoreMaxAge(t, a, 86400)

	// Log in, capturing the cookie the client keeps.
	loginReq, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	loginRR := httptest.NewRecorder()
	s, _ := a.sessions.Get(loginReq, a.SessionName())
	s.Values[constants.SessionClaims] = types.Claims{Sub: "foo"}
	assert.NoError(t, a.sessions.Save(loginReq, loginRR, s))
	assert.FileExists(t, sessionPath(s.ID))
	staleCookie := lastSessionCookie(t, a, loginRR)

	// Signing out deletes the session but leaves the client's cookie behind.
	assert.NoError(t, os.Remove(sessionPath(s.ID)))

	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	req.AddCookie(&http.Cookie{Name: staleCookie.Name, Value: staleCookie.Value})
	rr := httptest.NewRecorder()

	// checkAuth runs first and finds nothing, then the auth start mints a state.
	assert.Nil(t, a.getClaimsFromSession(rr, req))
	state, err := a.createState(req, rr, "/redirect")
	assert.NoError(t, err)

	parsed := parseState(t, a, state)
	assert.NotEqual(t, s.ID, parsed.SessionID, "state must not reference the signed-out session")
	assert.FileExists(t, sessionPath(parsed.SessionID))

	// Set-Cookie headers are applied in order, so the last one is what the
	// client keeps into the callback.
	cookie := lastSessionCookie(t, a, rr)
	assert.Greater(t, cookie.MaxAge, 0, "Expected a persisting session cookie, not a deletion")
	assert.NotEmpty(t, cookie.Value)
}
