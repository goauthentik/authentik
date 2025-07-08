package sqlitestore

import (
	"context"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"
	"time"

	"github.com/gorilla/sessions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
)

func TestNewSQLiteStore(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	assert.NoError(t, err)
	assert.NotNil(t, store)
	defer store.Close()

	// Verify database file was created
	assert.FileExists(t, dbPath)
}

func TestNewSQLiteStoreInvalidPath(t *testing.T) {
	// Test with invalid path (directory doesn't exist and can't be created)
	invalidPath := "/root/nonexistent/dir/sessions.sqlite"
	providerID := "test-provider"

	store, err := NewSQLiteStore(invalidPath, providerID, nil)
	if err != nil {
		// This is expected if we don't have permissions
		assert.Error(t, err)
		assert.Nil(t, store)
	} else {
		// If it succeeds, clean up
		store.Close()
	}
}

func TestSQLiteStoreWithOptions(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	options := &sessions.Options{
		Path:     "/test",
		MaxAge:   3600,
		HttpOnly: true,
		Secure:   true,
	}

	store, err := NewSQLiteStore(dbPath, providerID, options)
	assert.NoError(t, err)
	assert.NotNil(t, store)
	defer store.Close()
}

func TestSQLiteStoreClose(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	require.NotNil(t, store)

	// Close should not error
	err = store.Close()
	assert.NoError(t, err)

	// Multiple closes should not error
	err = store.Close()
	assert.NoError(t, err)
}

func TestSQLiteStoreGetNewSession(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/", nil)
	session, err := store.Get(req, "test-session")

	assert.NoError(t, err)
	assert.NotNil(t, session)
	assert.True(t, session.IsNew)
	assert.Equal(t, "test-session", session.Name())
}

func TestSQLiteStoreGetExistingSession(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Create and save a session first
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "test-session")
	require.NoError(t, err)

	session.Values["test-key"] = "test-value"
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Get the session ID from the cookie
	cookies := resp.Result().Cookies()
	require.Len(t, cookies, 1)
	sessionID := cookies[0].Value

	// Create new request with the session cookie
	req2 := httptest.NewRequest("GET", "/", nil)
	req2.AddCookie(&http.Cookie{
		Name:  "test-session",
		Value: sessionID,
	})

	// Get the existing session
	session2, err := store.Get(req2, "test-session")
	assert.NoError(t, err)
	assert.NotNil(t, session2)
	assert.False(t, session2.IsNew)
	assert.Equal(t, "test-value", session2.Values["test-key"])
}

func TestSQLiteStoreNew(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/", nil)
	session, err := store.New(req, "new-session")
	require.NoError(t, err)

	assert.NotNil(t, session)
	assert.True(t, session.IsNew)
	assert.Equal(t, "new-session", session.Name())
}

func TestSQLiteStoreSaveSession(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "save-test")
	require.NoError(t, err)

	session.Values["key1"] = "value1"
	session.Values["key2"] = 42
	session.Values["key3"] = map[string]string{"nested": "value"}

	err = store.Save(req, resp, session)
	assert.NoError(t, err)

	// Verify cookie was set
	cookies := resp.Result().Cookies()
	assert.Len(t, cookies, 1)
	assert.Equal(t, "save-test", cookies[0].Name)
	assert.NotEmpty(t, cookies[0].Value)
}

func TestSQLiteStoreSaveSessionWithExpiry(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "expiry-test")
	require.NoError(t, err)

	// Set session to expire in 1 hour
	session.Options.MaxAge = 3600
	session.Values["test"] = "data"

	err = store.Save(req, resp, session)
	assert.NoError(t, err)

	// Verify cookie has correct max age
	cookies := resp.Result().Cookies()
	assert.Len(t, cookies, 1)
	assert.Equal(t, 3600, cookies[0].MaxAge)
}

func TestSQLiteStoreSaveSessionDelete(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	// Create and save session
	session, err := store.Get(req, "delete-test")
	require.NoError(t, err)
	session.Values["test"] = "data"
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Get session ID
	cookies := resp.Result().Cookies()
	require.Len(t, cookies, 1)
	sessionID := cookies[0].Value

	// Create new request with session cookie
	req2 := httptest.NewRequest("GET", "/", nil)
	req2.AddCookie(&http.Cookie{
		Name:  "delete-test",
		Value: sessionID,
	})

	// Get session and mark for deletion
	resp2 := httptest.NewRecorder()
	session2, err := store.Get(req2, "delete-test")
	require.NoError(t, err)
	session2.Options.MaxAge = -1

	// Save (delete) the session
	err = store.Save(req2, resp2, session2)
	assert.NoError(t, err)

	// Verify cookie was deleted (MaxAge = -1)
	cookies = resp2.Result().Cookies()
	assert.Len(t, cookies, 1)
	assert.Equal(t, -1, cookies[0].MaxAge)

	// Try to get the deleted session
	req3 := httptest.NewRequest("GET", "/", nil)
	req3.AddCookie(&http.Cookie{
		Name:  "delete-test",
		Value: sessionID,
	})

	session3, err := store.Get(req3, "delete-test")
	assert.NoError(t, err)
	assert.True(t, session3.IsNew, "Session should be new after deletion")
	assert.Empty(t, session3.Values["test"], "Session data should be empty after deletion")
}

func TestSQLiteStoreCleanup(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Create and save a session that expires immediately
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "expired-session")
	require.NoError(t, err)
	session.Values["test"] = "data"
	session.Options.MaxAge = 1 // 1 second
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Wait for session to expire
	time.Sleep(2 * time.Second)

	// Run cleanup
	err = store.cleanup()
	assert.NoError(t, err)

	// Verify session was deleted
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestSQLiteStoreCleanupExpiredNoSessions(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Run cleanup with no sessions
	err = store.cleanup()
	assert.NoError(t, err)
}

func TestSQLiteStoreStartPeriodicCleanup(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start periodic cleanup with a short interval
	store.StartPeriodicCleanup(ctx, 1)

	// Create and save a session that expires immediately
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "expired-session")
	require.NoError(t, err)
	session.Values["test"] = "data"
	session.Options.MaxAge = 1 // 1 second
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Wait for cleanup to run
	time.Sleep(3 * time.Second)

	// Verify session was deleted by the cleanup routine
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestSQLiteStoreStartPeriodicCleanupCancellation(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	ctx, cancel := context.WithCancel(context.Background())

	// Start periodic cleanup
	store.StartPeriodicCleanup(ctx, 1)

	// Cancel the context immediately
	cancel()

	// Wait a moment for cancellation to take effect
	time.Sleep(100 * time.Millisecond)

	// Create and save a session that expires immediately
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "expired-session")
	require.NoError(t, err)
	session.Values["test"] = "data"
	session.Options.MaxAge = 1 // 1 second
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Wait for a bit
	time.Sleep(2 * time.Second)

	// Verify session was NOT deleted (cleanup was cancelled)
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(1), count, "Session should still exist as cleanup was cancelled")
}

func TestSQLiteStoreTableCreation(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Check if the table exists by trying to count records
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestSQLiteStoreGetAllSessions(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Create and save two sessions
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session1, err := store.Get(req, "session1")
	require.NoError(t, err)
	session1.Values["key"] = "value1"
	err = store.Save(req, resp, session1)
	require.NoError(t, err)

	session2, err := store.Get(req, "session2")
	require.NoError(t, err)
	session2.Values["key"] = "value2"
	err = store.Save(req, resp, session2)
	require.NoError(t, err)

	// Get all sessions
	sessions, err := store.GetAllSessions(context.Background())
	assert.NoError(t, err)
	assert.Len(t, sessions, 2)

	// Verify session values
	var values []string
	for _, s := range sessions {
		if val, ok := s.Values["key"].(string); ok {
			values = append(values, val)
		}
	}
	assert.Contains(t, values, "value1")
	assert.Contains(t, values, "value2")
}

func TestSQLiteStoreDeleteSession(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Create and save a session
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()

	session, err := store.Get(req, "delete-session")
	require.NoError(t, err)
	session.Values["key"] = "value"
	err = store.Save(req, resp, session)
	require.NoError(t, err)

	// Delete the session
	err = store.Delete(context.Background(), session)
	assert.NoError(t, err)

	// Verify session was deleted
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestSQLiteStoreCleanupExpired(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Create an expired session directly in the database
	expiredTime := time.Now().Add(-1 * time.Hour)
	expiredSession := sessionstore.ProxySession{
		UUID:       "expired-uuid",
		SessionKey: "expired-key",
		Data:       []byte("data"),
		Expires:    &expiredTime,
		Expiring:   true,
		ProviderID: providerID,
		Claims:     "{}",
		CreatedAt:  time.Now().Add(-2 * time.Hour),
	}

	// Create a valid session directly in the database
	validTime := time.Now().Add(1 * time.Hour)
	validSession := sessionstore.ProxySession{
		UUID:       "valid-uuid",
		SessionKey: "valid-key",
		Data:       []byte("data"),
		Expires:    &validTime,
		Expiring:   true,
		ProviderID: providerID,
		Claims:     "{}",
		CreatedAt:  time.Now(),
	}

	// Insert both sessions
	result := store.db.Create(&expiredSession)
	require.NoError(t, result.Error)
	result = store.db.Create(&validSession)
	require.NoError(t, result.Error)

	// Run cleanup
	err = store.cleanup()
	assert.NoError(t, err)

	// Verify only expired session was deleted
	var count int64
	result = store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)
	assert.Equal(t, int64(1), count)

	// Verify the remaining session is the valid one
	var remainingSession sessionstore.ProxySession
	result = store.db.First(&remainingSession)
	assert.NoError(t, result.Error)
	assert.Equal(t, "valid-uuid", remainingSession.UUID)
}

func TestSQLiteStoreReconnect(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_sessions.sqlite")
	providerID := "test-provider"

	store, err := NewSQLiteStore(dbPath, providerID, nil)
	require.NoError(t, err)
	defer store.Close()

	// Force close the database
	sqlDB, err := store.db.DB()
	require.NoError(t, err)
	err = sqlDB.Close()
	require.NoError(t, err)
	store.closed = true

	// Try to save a session, which should trigger reconnect
	req := httptest.NewRequest("GET", "/", nil)
	resp := httptest.NewRecorder()
	session, err := store.New(req, "reconnect-test")
	require.NoError(t, err)
	session.Values["test"] = "data"

	err = store.Save(req, resp, session)
	assert.NoError(t, err)
	assert.False(t, store.closed, "Store should no longer be marked as closed after reconnect")
}
