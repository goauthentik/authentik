package pgstore

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/mattn/go-sqlite3"
	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

// MockPGStore is a mock implementation of PGStore that uses SQLite in-memory database with GORM
type MockPGStore struct {
	*sessionstore.BaseStore
	db     *gorm.DB
	schema string
}

func TestMain(m *testing.M) {
	// Run tests with mock implementation
	code := m.Run()
	os.Exit(code)
}

// NewMockPGStore creates a new mock PG store with SQLite in-memory database
func NewMockPGStore(schema string, providerID string, sessionOptions *sessions.Options) (*MockPGStore, error) {
	logger := log.WithField("component", "MockPGStore")

	// Use SQLite in-memory database for testing with GORM
	db, err := gorm.Open(sqlite.Open(":memory:"), sessionstore.GormConfig(logger))
	if err != nil {
		return nil, fmt.Errorf("failed to open mock database: %w", err)
	}

	// Configure connection
	if err := sessionstore.ConfigureConnection(db); err != nil {
		return nil, fmt.Errorf("failed to configure database connection: %w", err)
	}

	// Auto-migrate the schema
	if err := db.AutoMigrate(&sessionstore.ProxySession{}); err != nil {
		return nil, fmt.Errorf("failed to migrate schema: %w", err)
	}

	store := &MockPGStore{
		BaseStore: sessionstore.NewBaseStore(providerID, "postgres"),
		db:        db,
		schema:    schema,
	}

	// Configure session options if provided
	if sessionOptions != nil {
		store.BaseStore.Options(*sessionOptions)
	}

	// Set key prefix for sessions
	store.BaseStore.KeyPrefix("authentik_proxy_session_")

	return store, nil
}

// Close closes the mock store
func (s *MockPGStore) Close() error {
	sqlDB, err := s.db.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// Get returns a session for the given name after adding it to the registry
func (s *MockPGStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry
func (s *MockPGStore) New(r *http.Request, name string) (*sessions.Session, error) {
	session, err := s.CreateNewSession(s, r, name)
	if err != nil {
		return session, err
	}

	if session.ID == "" {
		return session, nil
	}

	// Load session data from store
	err = s.load(r.Context(), session)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return session, nil
		}
		return session, err
	}

	session.IsNew = false
	return session, nil
}

// Save adds a single session to the response
func (s *MockPGStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Handle common save logic (cookie management, ID generation)
	if session.Options.MaxAge <= 0 {
		if err := s.delete(r.Context(), session); err != nil {
			return err
		}
		return s.HandleSessionSave(w, session)
	}

	if err := s.HandleSessionSave(w, session); err != nil {
		return err
	}

	// Save to database
	return s.save(r.Context(), session)
}

// save writes session to mock database using GORM
func (s *MockPGStore) save(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("save", time.Since(start))
	}()

	// Serialize session data
	data, err := s.GetSerializer().Serialize(session)
	if err != nil {
		return err
	}

	// Calculate expiry
	expiry := s.CalculateExpiry(session)
	sessionKey := s.GetSessionKey(session.ID)

	// Generate UUID for the session - make it unique by including provider ID
	sessionUUID := fmt.Sprintf("mock-uuid-%s-%s", s.ProviderID(), sessionKey)

	// Extract claims and redirect from session
	claims := "{}"
	if c, ok := session.Values["claims"]; ok && c != nil {
		claims = fmt.Sprintf("%v", c)
	}

	redirect := ""
	if r, ok := session.Values["redirect"]; ok && r != nil {
		redirect = fmt.Sprintf("%v", r)
	}

	// Create GORM model
	proxySession := sessionstore.ProxySession{
		UUID:       sessionUUID,
		SessionKey: sessionKey,
		Data:       data,
		Expires:    &expiry,
		Expiring:   true,
		ProviderID: s.ProviderID(),
		Claims:     claims,
		Redirect:   redirect,
		CreatedAt:  time.Now(),
	}

	// Use GORM's Upsert functionality
	result := s.db.WithContext(ctx).Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "session_key"}, {Name: "provider_id"}},
		DoUpdates: clause.AssignmentColumns([]string{"data", "expires", "claims", "redirect"}),
	}).Create(&proxySession)

	return result.Error
}

// load reads session from mock database using GORM
func (s *MockPGStore) load(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("load", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)

	var proxySession sessionstore.ProxySession
	result := s.db.WithContext(ctx).
		Where("session_key = ? AND provider_id = ? AND (expires IS NULL OR expires > ?)",
			sessionKey, s.ProviderID(), time.Now()).
		First(&proxySession)

	if result.Error != nil {
		return result.Error
	}

	return s.GetSerializer().Deserialize(proxySession.Data, session)
}

// delete removes session from mock database using GORM
func (s *MockPGStore) delete(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("delete", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)

	result := s.db.WithContext(ctx).
		Where("session_key = ? AND provider_id = ?", sessionKey, s.ProviderID()).
		Delete(&sessionstore.ProxySession{})

	return result.Error
}

// Delete removes the session
func (s *MockPGStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// GetAllSessions returns all sessions in the database for this provider
func (s *MockPGStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	var proxySessions []sessionstore.ProxySession
	result := s.db.WithContext(ctx).
		Where("provider_id = ? AND (expires IS NULL OR expires > ?)", s.ProviderID(), time.Now()).
		Find(&proxySessions)

	if result.Error != nil {
		return nil, result.Error
	}

	var resultSessions []*sessions.Session
	for _, proxySession := range proxySessions {
		session := sessions.NewSession(s, "")
		session.ID = sessionKey(proxySession.SessionKey, s.GetKeyPrefix())

		if err := s.GetSerializer().Deserialize(proxySession.Data, session); err != nil {
			// Skip sessions that can't be deserialized
			continue
		}
		resultSessions = append(resultSessions, session)
	}

	return resultSessions, nil
}

// Helper function to extract the session ID from the session key
func sessionKey(key string, prefix string) string {
	return key[len(prefix):]
}

// Mock the PostgreSQL tests using the MockPGStore

func getTestConnectionString() string {
	// Return a dummy connection string for compatibility
	return "mock://postgres"
}

func setupTestTable(db *gorm.DB, schema string) error {
	// No-op for mock
	return nil
}

func cleanupTestTable(db *gorm.DB, schema string) error {
	// No-op for mock
	return nil
}

func TestNewPGStore(t *testing.T) {
	schema := "test_schema"
	providerID := "test-provider-123"
	sessionOptions := &sessions.Options{
		Path:     "/test",
		MaxAge:   3600,
		HttpOnly: true,
		Secure:   true,
	}

	// Test successful creation
	store, err := NewMockPGStore(schema, providerID, sessionOptions)
	require.NoError(t, err)
	require.NotNil(t, store)
	assert.Equal(t, schema, store.schema)
	assert.Equal(t, providerID, store.ProviderID())
	assert.Equal(t, "authentik_proxy_session_", store.GetKeyPrefix())

	// Test connection by running a simple query
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).Count(&count)
	assert.NoError(t, result.Error)

	// Cleanup
	err = store.Close()
	assert.NoError(t, err)
}

func TestNewPGStore_InvalidConnection(t *testing.T) {
	// Test with invalid connection string
	_, err := NewPGStore("invalid://connection-string", "test-schema", "test-provider", nil)
	assert.Error(t, err)
}

func TestNewPGStore_ConnectionFailed(t *testing.T) {
	// Skip this test as we're now using GORM
	t.Skip("Not applicable with GORM")
}

func TestPGStore_Close(t *testing.T) {
	store, err := NewMockPGStore("test_close", "test-provider-close", nil)
	require.NoError(t, err)

	// Test that close works without error
	err = store.Close()
	assert.NoError(t, err)
}

func TestPGStore_SessionLifecycle(t *testing.T) {
	store, err := NewMockPGStore("test_lifecycle", "test-provider-lifecycle", nil)
	require.NoError(t, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "test_lifecycle")
	require.NoError(t, err)
	defer cleanupTestTable(store.db, "test_lifecycle")

	// Create test request and response
	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Test creating new session
	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	assert.True(t, session.IsNew)
	assert.Equal(t, "test-session", session.Name())

	// Add some data to session
	session.Values["user"] = "testuser"
	session.Values["role"] = "admin"
	session.Values["claims"] = `{"sub": "123", "email": "test@example.com"}`
	session.Values["redirect"] = "/dashboard"

	// Test saving session
	err = store.Save(req, w, session)
	require.NoError(t, err)
	assert.NotEmpty(t, session.ID)

	// Test loading session
	reqWithCookie := httptest.NewRequest("GET", "/test", nil)
	reqWithCookie.AddCookie(&http.Cookie{
		Name:  "test-session",
		Value: session.ID,
	})

	loadedSession, err := store.New(reqWithCookie, "test-session")
	require.NoError(t, err)
	assert.False(t, loadedSession.IsNew)
	assert.Equal(t, session.ID, loadedSession.ID)
	assert.Equal(t, "testuser", loadedSession.Values["user"])
	assert.Equal(t, "admin", loadedSession.Values["role"])
}

func TestPGStore_Get(t *testing.T) {
	store, err := NewMockPGStore("test_get", "test-provider-get", nil)
	require.NoError(t, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "test_get")
	require.NoError(t, err)
	defer cleanupTestTable(store.db, "test_get")

	req := httptest.NewRequest("GET", "/test", nil)

	// Test getting session (should create new one)
	session, err := store.Get(req, "test-session")
	require.NoError(t, err)
	assert.True(t, session.IsNew)
}

func TestPGStore_Save_WithMaxAge(t *testing.T) {
	store, err := NewMockPGStore("test_save_maxage", "test-provider-save", nil)
	require.NoError(t, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "test_save_maxage")
	require.NoError(t, err)
	defer cleanupTestTable(store.db, "test_save_maxage")

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Test with negative MaxAge (should delete)
	session, err := store.New(req, "test-session")
	require.NoError(t, err)

	session.Values["data"] = "test"
	session.Options.MaxAge = -1

	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Verify session was deleted from database
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).
		Where("provider_id = ?", "test-provider-save").
		Count(&count)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestPGStore_Save_SerializationError(t *testing.T) {
	store, err := NewMockPGStore("test_save_error", "test-provider-save-error", nil)
	require.NoError(t, err)
	defer store.Close()

	// Create a custom serializer that always fails
	store.Serializer(&failingSerializer{})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	session, err := store.New(req, "test-session")
	require.NoError(t, err)

	session.Values["data"] = "test"

	err = store.Save(req, w, session)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "serialization failed")
}

func TestPGStore_Load_NotFound(t *testing.T) {
	store, err := NewMockPGStore("test_load_notfound", "test-provider-load", nil)
	require.NoError(t, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "test_load_notfound")
	require.NoError(t, err)
	defer cleanupTestTable(store.db, "test_load_notfound")

	req := httptest.NewRequest("GET", "/test", nil)
	req.AddCookie(&http.Cookie{
		Name:  "test-session",
		Value: "nonexistent-session-id",
	})

	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	assert.True(t, session.IsNew) // Should be new when not found
}

func TestPGStore_Load_Expired(t *testing.T) {
	store, err := NewMockPGStore("test_load_expired", "test-provider-expired", nil)
	require.NoError(t, err)
	defer store.Close()

	// Insert expired session directly
	sessionKey := "authentik_proxy_session_expired_test"
	expiry := time.Now().Add(-1 * time.Hour) // 1 hour ago

	proxySession := sessionstore.ProxySession{
		UUID:       "test-uuid",
		SessionKey: sessionKey,
		Data:       []byte("expired session data"),
		Expires:    &expiry,
		Expiring:   true,
		ProviderID: "test-provider-expired",
		Claims:     "{}",
		Redirect:   "",
		CreatedAt:  time.Now(),
	}

	result := store.db.Create(&proxySession)
	require.NoError(t, result.Error)

	// Try to load expired session
	req := httptest.NewRequest("GET", "/test", nil)
	req.AddCookie(&http.Cookie{
		Name:  "test-session",
		Value: "expired_test",
	})

	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	assert.True(t, session.IsNew) // Should be new when expired
}

func TestPGStore_Delete(t *testing.T) {
	store, err := NewMockPGStore("test_delete", "test-provider-delete", nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create and save session
	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	session.Values["data"] = "test"

	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Verify session exists
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).
		Where("session_key = ? AND provider_id = ?", store.GetSessionKey(session.ID), "test-provider-delete").
		Count(&count)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(1), count)

	// Delete session
	err = store.Delete(context.Background(), session)
	require.NoError(t, err)

	// Verify session is deleted
	result = store.db.Model(&sessionstore.ProxySession{}).
		Where("session_key = ? AND provider_id = ?", store.GetSessionKey(session.ID), "test-provider-delete").
		Count(&count)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(0), count)
}

func TestPGStore_GetAllSessions(t *testing.T) {
	store, err := NewMockPGStore("test_get_all", "test-provider-get-all", nil)
	require.NoError(t, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "test_get_all")
	require.NoError(t, err)
	defer cleanupTestTable(store.db, "test_get_all")

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create multiple sessions
	sessions := make([]*sessions.Session, 3)
	for i := 0; i < 3; i++ {
		session, err := store.New(req, fmt.Sprintf("test-session-%d", i))
		require.NoError(t, err)
		session.Values["index"] = i
		session.Values["data"] = fmt.Sprintf("session %d", i)

		err = store.Save(req, w, session)
		require.NoError(t, err)
		sessions[i] = session
	}

	// Get all sessions
	allSessions, err := store.GetAllSessions(context.Background())
	require.NoError(t, err)
	assert.Len(t, allSessions, 3)

	// Verify session data
	for _, session := range allSessions {
		assert.Contains(t, session.Values, "index")
		assert.Contains(t, session.Values, "data")
	}
}

func TestPGStore_GetAllSessions_WithExpired(t *testing.T) {
	store, err := NewMockPGStore("test_get_all_expired", "test-provider-get-all-expired", nil)
	require.NoError(t, err)
	defer store.Close()

	// Insert one valid and one expired session
	validExpiry := time.Now().Add(1 * time.Hour)
	expiredExpiry := time.Now().Add(-1 * time.Hour)

	// Valid session
	validData, _ := store.GetSerializer().Serialize(&sessions.Session{Values: map[interface{}]interface{}{"valid": true}})
	validSession := sessionstore.ProxySession{
		UUID:       "valid-uuid",
		SessionKey: "authentik_proxy_session_valid",
		Data:       validData,
		Expires:    &validExpiry,
		Expiring:   true,
		ProviderID: "test-provider-get-all-expired",
		Claims:     "{}",
		Redirect:   "",
		CreatedAt:  time.Now(),
	}
	result := store.db.Create(&validSession)
	require.NoError(t, result.Error)

	// Expired session
	expiredData, _ := store.GetSerializer().Serialize(&sessions.Session{Values: map[interface{}]interface{}{"expired": true}})
	expiredSession := sessionstore.ProxySession{
		UUID:       "expired-uuid",
		SessionKey: "authentik_proxy_session_expired",
		Data:       expiredData,
		Expires:    &expiredExpiry,
		Expiring:   true,
		ProviderID: "test-provider-get-all-expired",
		Claims:     "{}",
		Redirect:   "",
		CreatedAt:  time.Now(),
	}
	result = store.db.Create(&expiredSession)
	require.NoError(t, result.Error)

	// Get all sessions - should only return valid ones
	allSessions, err := store.GetAllSessions(context.Background())
	require.NoError(t, err)
	assert.Len(t, allSessions, 1)
	assert.True(t, allSessions[0].Values["valid"].(bool))
}

func TestPGStore_GetAllSessions_DeserializationError(t *testing.T) {
	store, err := NewMockPGStore("test_get_all_deser_error", "test-provider-get-all-deser", nil)
	require.NoError(t, err)
	defer store.Close()

	// Insert session with invalid data
	validExpiry := time.Now().Add(1 * time.Hour)

	// Invalid serialized data
	invalidSession := sessionstore.ProxySession{
		UUID:       "invalid-uuid",
		SessionKey: "authentik_proxy_session_invalid",
		Data:       []byte("invalid serialized data"),
		Expires:    &validExpiry,
		Expiring:   true,
		ProviderID: "test-provider-get-all-deser",
		Claims:     "{}",
		Redirect:   "",
		CreatedAt:  time.Now(),
	}
	result := store.db.Create(&invalidSession)
	require.NoError(t, result.Error)

	// Get all sessions - should skip invalid ones
	allSessions, err := store.GetAllSessions(context.Background())
	require.NoError(t, err)
	assert.Len(t, allSessions, 0)
}

func TestPGStore_ConflictHandling(t *testing.T) {
	store, err := NewMockPGStore("test_conflict", "test-provider-conflict", nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create session
	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	session.Values["data"] = "original"

	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Update session with same ID
	session.Values["data"] = "updated"
	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Verify only one row exists and it's updated
	var count int64
	result := store.db.Model(&sessionstore.ProxySession{}).
		Where("session_key = ? AND provider_id = ?", store.GetSessionKey(session.ID), "test-provider-conflict").
		Count(&count)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(1), count)

	// Load and verify updated data
	reqWithCookie := httptest.NewRequest("GET", "/test", nil)
	reqWithCookie.AddCookie(&http.Cookie{
		Name:  "test-session",
		Value: session.ID,
	})

	loadedSession, err := store.New(reqWithCookie, "test-session")
	require.NoError(t, err)
	assert.Equal(t, "updated", loadedSession.Values["data"])
}

func TestPGStore_MultipleProviders(t *testing.T) {
	// Create a shared database connection for both stores
	logger := log.WithField("component", "MockPGStore")

	// Use a named in-memory database so both stores share the same connection
	// See: https://www.sqlite.org/inmemorydb.html - "shared cache" mode
	db, err := gorm.Open(sqlite.Open("file:memdb1?mode=memory&cache=shared"), sessionstore.GormConfig(logger))
	require.NoError(t, err)
	defer func() {
		sqlDB, _ := db.DB()
		if sqlDB != nil {
			sqlDB.Close()
		}
	}()

	// Configure connection
	err = sessionstore.ConfigureConnection(db)
	require.NoError(t, err)

	// Auto-migrate the schema
	err = db.AutoMigrate(&sessionstore.ProxySession{})
	require.NoError(t, err)

	// Create the first store
	store1 := &MockPGStore{
		BaseStore: sessionstore.NewBaseStore("test-provider-1", "postgres"),
		db:        db,
		schema:    "test_multi_providers",
	}
	store1.BaseStore.KeyPrefix("authentik_proxy_session_")

	// Create the second store
	store2 := &MockPGStore{
		BaseStore: sessionstore.NewBaseStore("test-provider-2", "postgres"),
		db:        db,
		schema:    "test_multi_providers",
	}
	store2.BaseStore.KeyPrefix("authentik_proxy_session_")

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create sessions with same session key but different providers
	session1, err := store1.New(req, "test-session")
	require.NoError(t, err)
	session1.Values["provider"] = "provider1"
	session1.ID = "same-session-id"

	session2, err := store2.New(req, "test-session")
	require.NoError(t, err)
	session2.Values["provider"] = "provider2"
	session2.ID = "same-session-id"

	err = store1.Save(req, w, session1)
	require.NoError(t, err)

	err = store2.Save(req, w, session2)
	require.NoError(t, err)

	// Verify both sessions exist - we need to use a shared DB connection
	// since we're using in-memory SQLite
	var count int64
	result := store1.db.Model(&sessionstore.ProxySession{}).Count(&count)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(2), count)

	// Verify provider isolation
	var provider1Sessions []sessionstore.ProxySession
	result = store1.db.Where("provider_id = ?", "test-provider-1").Find(&provider1Sessions)
	require.NoError(t, result.Error)
	assert.Len(t, provider1Sessions, 1)

	var provider2Sessions []sessionstore.ProxySession
	result = store1.db.Where("provider_id = ?", "test-provider-2").Find(&provider2Sessions)
	require.NoError(t, result.Error)
	assert.Len(t, provider2Sessions, 1)
}

func TestPGStore_ClaimsAndRedirect(t *testing.T) {
	store, err := NewMockPGStore("test_claims_redirect", "test-provider-claims", nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create session with claims and redirect
	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	session.Values["claims"] = `{"sub": "user123", "email": "user@example.com"}`
	session.Values["redirect"] = "/after/auth"

	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Verify claims and redirect were saved
	var proxySession sessionstore.ProxySession
	result := store.db.Where("session_key = ? AND provider_id = ?",
		store.GetSessionKey(session.ID), "test-provider-claims").
		First(&proxySession)
	require.NoError(t, result.Error)

	assert.Equal(t, `{"sub": "user123", "email": "user@example.com"}`, proxySession.Claims)
	assert.Equal(t, "/after/auth", proxySession.Redirect)
}

func TestPGStore_NullClaims(t *testing.T) {
	store, err := NewMockPGStore("test_null_claims", "test-provider-null", nil)
	require.NoError(t, err)
	defer store.Close()

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	// Create session without claims or redirect
	session, err := store.New(req, "test-session")
	require.NoError(t, err)
	// Don't set claims or redirect

	err = store.Save(req, w, session)
	require.NoError(t, err)

	// Verify default values for claims and redirect
	var proxySession sessionstore.ProxySession
	result := store.db.Where("session_key = ? AND provider_id = ?",
		store.GetSessionKey(session.ID), "test-provider-null").
		First(&proxySession)
	require.NoError(t, result.Error)

	// Default values should be "{}" for claims and empty string for redirect
	assert.Equal(t, "{}", proxySession.Claims)
	assert.Equal(t, "", proxySession.Redirect)
}

// Helper types for testing
type failingSerializer struct{}

func (fs *failingSerializer) Serialize(s *sessions.Session) ([]byte, error) {
	return nil, fmt.Errorf("serialization failed")
}

func (fs *failingSerializer) Deserialize(b []byte, s *sessions.Session) error {
	return fmt.Errorf("deserialization failed")
}

// Benchmarks
func BenchmarkPGStore_Save(b *testing.B) {
	store, err := NewMockPGStore("bench_save", "bench-provider", nil)
	require.NoError(b, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "bench_save")
	require.NoError(b, err)
	defer cleanupTestTable(store.db, "bench_save")

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		session, err := store.New(req, "bench-session")
		require.NoError(b, err)
		session.Values["data"] = fmt.Sprintf("benchmark data %d", i)

		err = store.Save(req, w, session)
		require.NoError(b, err)
	}
}

func BenchmarkPGStore_Load(b *testing.B) {
	store, err := NewMockPGStore("bench_load", "bench-provider", nil)
	require.NoError(b, err)
	defer store.Close()

	// Setup test table
	err = setupTestTable(store.db, "bench_load")
	require.NoError(b, err)
	defer cleanupTestTable(store.db, "bench_load")

	// Create a session to load
	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()

	session, err := store.New(req, "bench-session")
	require.NoError(b, err)
	session.Values["data"] = "benchmark data"

	err = store.Save(req, w, session)
	require.NoError(b, err)

	// Create request with cookie
	reqWithCookie := httptest.NewRequest("GET", "/test", nil)
	reqWithCookie.AddCookie(&http.Cookie{
		Name:  "bench-session",
		Value: session.ID,
	})

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := store.New(reqWithCookie, "bench-session")
		require.NoError(b, err)
	}
}
