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
)

func TestLogout(t *testing.T) {
	a := newTestApplication()
	_ = a.configureProxy()
	req, _ := http.NewRequest("GET", "https://ext.t.goauthentik.io/foo", nil)
	rr := httptest.NewRecorder()

	// Login once
	s, _ := a.sessions.Get(req, constants.SessionName)
	s.ID = uuid.New().String()
	s.Options.MaxAge = 86400
	s.Values[constants.SessionClaims] = Claims{
		Sub: "foo",
	}
	err := a.sessions.Save(req, rr, s)
	if err != nil {
		panic(err)
	}

	a.mux.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusBadGateway, rr.Code)

	// Login twice
	s2, _ := a.sessions.Get(req, constants.SessionName)
	s2.ID = uuid.New().String()
	s2.Options.MaxAge = 86400
	s2.Values[constants.SessionClaims] = Claims{
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
	s3, _ := a.sessions.Get(req, constants.SessionName)
	s3.ID = uuid.New().String()
	s3.Options.MaxAge = 86400
	s3.Values[constants.SessionClaims] = Claims{
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
