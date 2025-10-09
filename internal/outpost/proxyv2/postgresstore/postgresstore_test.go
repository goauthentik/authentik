package postgresstore

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// SetupTestDB creates a test database connection for testing
func SetupTestDB(t *testing.T) *gorm.DB {
	cfg := config.Get().PostgreSQL
	dsn, err := BuildDSN(cfg)
	require.NoError(t, err)

	// Configure GORM
	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	}

	db, err := gorm.Open(postgres.Open(dsn), gormConfig)
	require.NoError(t, err)

	// Auto-migrate the schema
	err = db.AutoMigrate(&ProxySession{})
	require.NoError(t, err)

	return db
}

// CleanupTestDB removes test sessions from the database
func CleanupTestDB(t *testing.T, db *gorm.DB) {
	db.Exec("DELETE FROM authentik_outposts_proxy_session")
}

func TestPostgresStore_New(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	req := httptest.NewRequest("GET", "/", nil)
	session, err := store.New(req, "test_session")

	assert.NoError(t, err)
	assert.True(t, session.IsNew)
	assert.Equal(t, "test_session", session.Name())
}

func TestPostgresStore_Save(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	req := httptest.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()
	session, err := store.New(req, "test_session")
	require.NoError(t, err)

	// Set up session claims
	userID := uuid.New()
	claims := map[string]interface{}{
		"sub":                userID.String(),
		"email":              "test@example.com",
		"preferred_username": "testuser",
		"exp":                time.Now().Add(time.Hour).Unix(),
		"custom_claim":       "custom_value",
	}
	session.Values[constants.SessionClaims] = claims

	err = store.Save(req, w, session)
	assert.NoError(t, err)

	// Verify session was saved to database
	var savedSession ProxySession
	err = db.First(&savedSession, "session_key = ?", session.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, userID, *savedSession.UserID)

	// Verify session data contains claims
	var sessionData map[string]interface{}
	err = json.Unmarshal([]byte(savedSession.SessionData), &sessionData)
	assert.NoError(t, err)

	claimsData, ok := sessionData[constants.SessionClaims].(map[string]interface{})
	assert.True(t, ok)
	assert.Equal(t, "test@example.com", claimsData["email"])
	assert.Equal(t, "testuser", claimsData["preferred_username"])
	assert.Equal(t, "custom_value", claimsData["custom_claim"])
}

func TestPostgresStore_Load(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create a session directly in the database
	userID := uuid.New()
	sessionKey := "test_session_123"

	sessionData := map[string]interface{}{
		constants.SessionClaims: map[string]interface{}{
			"sub":                userID.String(),
			"email":              "test@example.com",
			"preferred_username": "testuser",
			"exp":                time.Now().Add(time.Hour).Unix(),
			"custom_claim":       "custom_value",
		},
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
	}

	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	proxySession := ProxySession{
		SessionKey:  sessionKey,
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
	}
	err = db.Create(&proxySession).Error
	require.NoError(t, err)

	// Load the session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.load(session)
	assert.NoError(t, err)

	// Verify claims were loaded correctly
	claims, ok := session.Values[constants.SessionClaims].(map[string]interface{})
	assert.True(t, ok)
	assert.Equal(t, userID.String(), claims["sub"])
	assert.Equal(t, "test@example.com", claims["email"])
	assert.Equal(t, "testuser", claims["preferred_username"])
	assert.Equal(t, "custom_value", claims["custom_claim"])
}

func TestPostgresStore_Delete(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create a session in the database
	sessionKey := "test_session_456"
	sessionData := map[string]interface{}{
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
	}
	sessionDataJSON, _ := json.Marshal(sessionData)

	proxySession := ProxySession{
		SessionKey:  sessionKey,
		SessionData: string(sessionDataJSON),
	}
	err := db.Create(&proxySession).Error
	require.NoError(t, err)

	// Delete the session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.delete(session)
	assert.NoError(t, err)

	// Verify session was deleted
	var count int64
	db.Model(&ProxySession{}).Where("session_key = ?", sessionKey).Count(&count)
	assert.Equal(t, int64(0), count)
}

func TestPostgresStore_CleanupExpired(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create some sessions
	expiredData := map[string]interface{}{
		"_expires_at": time.Now().Add(-time.Hour).Format(time.RFC3339),
	}
	expiredDataJSON, _ := json.Marshal(expiredData)

	validData := map[string]interface{}{
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
	}
	validDataJSON, _ := json.Marshal(validData)

	expiredSession := ProxySession{
		SessionKey:  "test_expired_session",
		SessionData: string(expiredDataJSON),
	}
	validSession := ProxySession{
		SessionKey:  "test_valid_session",
		SessionData: string(validDataJSON),
	}

	err := db.Create(&expiredSession).Error
	require.NoError(t, err)
	err = db.Create(&validSession).Error
	require.NoError(t, err)

	// Clean up expired sessions
	err = store.CleanupExpired()
	assert.NoError(t, err)

	// Verify only valid session remains
	var count int64
	db.Model(&ProxySession{}).Where("session_key LIKE 'test_%'").Count(&count)
	assert.Equal(t, int64(1), count)

	var remaining ProxySession
	err = db.Where("session_key LIKE 'test_%'").First(&remaining).Error
	assert.NoError(t, err)
	assert.Equal(t, "test_valid_session", remaining.SessionKey)
}

func TestPostgresStore_LogoutSessions_ByUserID(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create multiple sessions for different users
	user1 := uuid.New()
	user2 := uuid.New()

	sessions := []ProxySession{
		{
			SessionKey: "test_session_user1_1",
			UserID:     &user1,
			SessionData: createSessionData(t, map[string]interface{}{
				"sub":   user1.String(),
				"email": "user1@example.com",
			}),
		},
		{
			SessionKey: "test_session_user1_2",
			UserID:     &user1,
			SessionData: createSessionData(t, map[string]interface{}{
				"sub":   user1.String(),
				"email": "user1@example.com",
			}),
		},
		{
			SessionKey: "test_session_user2_1",
			UserID:     &user2,
			SessionData: createSessionData(t, map[string]interface{}{
				"sub":   user2.String(),
				"email": "user2@example.com",
			}),
		},
	}

	for _, session := range sessions {
		err := db.Create(&session).Error
		require.NoError(t, err)
	}

	// Test filtering by user ID
	ctx := context.Background()
	err := store.LogoutSessions(ctx, func(c types.Claims) bool {
		return c.Sub == user1.String()
	})
	assert.NoError(t, err)

	// Verify only user2 session remains
	var count int64
	db.Model(&ProxySession{}).Where("session_key LIKE 'test_%'").Count(&count)
	assert.Equal(t, int64(1), count)

	var remaining ProxySession
	err = db.Where("session_key LIKE 'test_%'").First(&remaining).Error
	assert.NoError(t, err)
	assert.Equal(t, user2, *remaining.UserID)
}

func TestPostgresStore_LogoutSessions_ByEmail(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create sessions with different emails
	sessions := []ProxySession{
		{
			SessionKey: "test_session_admin_1",
			SessionData: createSessionData(t, map[string]interface{}{
				"email": "admin@example.com",
			}),
		},
		{
			SessionKey: "test_session_admin_2",
			SessionData: createSessionData(t, map[string]interface{}{
				"email": "admin@example.com",
			}),
		},
		{
			SessionKey: "test_session_user_1",
			SessionData: createSessionData(t, map[string]interface{}{
				"email": "user@example.com",
			}),
		},
	}

	for _, session := range sessions {
		err := db.Create(&session).Error
		require.NoError(t, err)
	}

	// Logout all admin sessions
	ctx := context.Background()
	err := store.LogoutSessions(ctx, func(c types.Claims) bool {
		return c.Email == "admin@example.com"
	})
	assert.NoError(t, err)

	// Verify only user session remains
	var count int64
	db.Model(&ProxySession{}).Where("session_key LIKE 'test_%'").Count(&count)
	assert.Equal(t, int64(1), count)

	var remaining ProxySession
	err = db.Where("session_key LIKE 'test_%'").First(&remaining).Error
	assert.NoError(t, err)

	var sessionData map[string]interface{}
	err = json.Unmarshal([]byte(remaining.SessionData), &sessionData)
	require.NoError(t, err)
	claims := sessionData[constants.SessionClaims].(map[string]interface{})
	assert.Equal(t, "user@example.com", claims["email"])
}

func TestPostgresStore_LogoutSessions_WithGroups(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create sessions with different group memberships
	sessions := []ProxySession{
		{
			SessionKey: "test_session_admin_user",
			SessionData: createSessionData(t, map[string]interface{}{
				"email":  "admin@example.com",
				"groups": []interface{}{"admin", "user"},
			}),
		},
		{
			SessionKey: "test_session_regular_user",
			SessionData: createSessionData(t, map[string]interface{}{
				"email":  "user@example.com",
				"groups": []interface{}{"user"},
			}),
		},
		{
			SessionKey: "test_session_guest",
			SessionData: createSessionData(t, map[string]interface{}{
				"email":  "guest@example.com",
				"groups": []interface{}{"guest"},
			}),
		},
	}

	for _, session := range sessions {
		err := db.Create(&session).Error
		require.NoError(t, err)
	}

	// Logout all sessions that have "admin" group
	ctx := context.Background()
	err := store.LogoutSessions(ctx, func(c types.Claims) bool {
		for _, group := range c.Groups {
			if group == "admin" {
				return true
			}
		}
		return false
	})
	assert.NoError(t, err)

	// Verify admin user session was removed
	var count int64
	db.Model(&ProxySession{}).Where("session_key LIKE 'test_%'").Count(&count)
	assert.Equal(t, int64(2), count)

	// Verify remaining sessions don't have admin group
	var remainingSessions []ProxySession
	err = db.Where("session_key LIKE 'test_%'").Find(&remainingSessions).Error
	assert.NoError(t, err)

	for _, session := range remainingSessions {
		var sessionData map[string]interface{}
		err := json.Unmarshal([]byte(session.SessionData), &sessionData)
		require.NoError(t, err)
		claims := sessionData[constants.SessionClaims].(map[string]interface{})
		assert.NotEqual(t, "admin@example.com", claims["email"])
	}
}

func TestPostgresStore_LoadExpiredSession(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create an expired session
	sessionKey := "test_expired_load"
	expiredData := map[string]interface{}{
		"_expires_at": time.Now().Add(-time.Hour).Format(time.RFC3339),
		constants.SessionClaims: map[string]interface{}{
			"sub": "test-user",
		},
	}
	expiredDataJSON, _ := json.Marshal(expiredData)

	proxySession := ProxySession{
		SessionKey:  sessionKey,
		SessionData: string(expiredDataJSON),
	}
	err := db.Create(&proxySession).Error
	require.NoError(t, err)

	// Try to load the expired session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.load(session)

	// Should return ErrRecordNotFound because session is expired
	assert.Error(t, err)
	assert.Equal(t, gorm.ErrRecordNotFound, err)

	// Verify the expired session was deleted
	var count int64
	db.Model(&ProxySession{}).Where("session_key = ?", sessionKey).Count(&count)
	assert.Equal(t, int64(0), count)
}

func TestPostgresStore_ConcurrentSessionAccess(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create a shared session ID
	sessionKey := "test_concurrent_session_" + uuid.New().String()

	// Initial session data
	initialData := map[string]interface{}{
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
		"counter":     0,
	}
	initialDataJSON, _ := json.Marshal(initialData)

	proxySession := ProxySession{
		SessionKey:  sessionKey,
		SessionData: string(initialDataJSON),
	}
	err := db.Create(&proxySession).Error
	require.NoError(t, err)

	// Simulate concurrent access from multiple goroutines
	const numGoroutines = 10
	done := make(chan bool, numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			defer func() { done <- true }()

			session := sessions.NewSession(store, "test_session")
			session.ID = sessionKey

			// Load session
			err := store.load(session)
			if err != nil {
				t.Logf("Goroutine %d failed to load: %v", id, err)
				return
			}

			// Modify session data
			session.Values["goroutine_"+string(rune('0'+id))] = id

			// Save session
			req := httptest.NewRequest("GET", "/", nil)
			w := httptest.NewRecorder()
			err = store.Save(req, w, session)
			if err != nil {
				t.Logf("Goroutine %d failed to save: %v", id, err)
			}
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < numGoroutines; i++ {
		<-done
	}

	// Verify session still exists and is valid
	var finalSession ProxySession
	err = db.Where("session_key = ?", sessionKey).First(&finalSession).Error
	assert.NoError(t, err)

	// Verify we can unmarshal the final session data
	var sessionData map[string]interface{}
	err = json.Unmarshal([]byte(finalSession.SessionData), &sessionData)
	assert.NoError(t, err)
}

func TestBuildDSN_Validation(t *testing.T) {
	tests := []struct {
		name        string
		cfg         config.PostgreSQLConfig
		expectError bool
		errorMsg    string
	}{
		{
			name: "missing host",
			cfg: config.PostgreSQLConfig{
				Port: 5432,
				User: "testuser",
				Name: "testdb",
			},
			expectError: true,
			errorMsg:    "PostgreSQL host is required",
		},
		{
			name: "missing user",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: 5432,
				Name: "testdb",
			},
			expectError: true,
			errorMsg:    "PostgreSQL user is required",
		},
		{
			name: "missing database name",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: 5432,
				User: "testuser",
			},
			expectError: true,
			errorMsg:    "PostgreSQL database name is required",
		},
		{
			name: "invalid port (zero)",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: 0,
				User: "testuser",
				Name: "testdb",
			},
			expectError: true,
			errorMsg:    "PostgreSQL port must be positive",
		},
		{
			name: "invalid port (negative)",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: -1,
				User: "testuser",
				Name: "testdb",
			},
			expectError: true,
			errorMsg:    "PostgreSQL port must be positive",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := BuildDSN(tt.cfg)
			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorMsg)
				assert.Empty(t, result)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestBuildDSN(t *testing.T) {
	tests := []struct {
		name     string
		cfg      config.PostgreSQLConfig
		expected string
	}{
		{
			name: "basic configuration",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: 5432,
				User: "testuser",
				Name: "testdb",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb sslmode=prefer",
		},
		{
			name: "with password",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: "testpass",
				Name:     "testdb",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb password=testpass sslmode=prefer",
		},
		{
			name: "with custom SSL mode",
			cfg: config.PostgreSQLConfig{
				Host:    "localhost",
				Port:    5432,
				User:    "testuser",
				Name:    "testdb",
				SSLMode: "require",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb sslmode=require",
		},
		{
			name: "with SSL certificates",
			cfg: config.PostgreSQLConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "testuser",
				Name:        "testdb",
				SSLMode:     "verify-full",
				SSLRootCert: "/path/to/root.crt",
				SSLCert:     "/path/to/client.crt",
				SSLKey:      "/path/to/client.key",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb sslmode=verify-full sslrootcert=/path/to/root.crt sslcert=/path/to/client.crt sslkey=/path/to/client.key",
		},
		{
			name: "with custom schema",
			cfg: config.PostgreSQLConfig{
				Host:          "localhost",
				Port:          5432,
				User:          "testuser",
				Name:          "testdb",
				DefaultSchema: "custom_schema",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb sslmode=prefer search_path=custom_schema",
		},
		{
			name: "with connection options",
			cfg: config.PostgreSQLConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "testuser",
				Name:        "testdb",
				ConnOptions: "connect_timeout=10",
			},
			expected: "host=localhost port=5432 user=testuser dbname=testdb sslmode=prefer connect_timeout=10",
		},
		{
			name: "full configuration",
			cfg: config.PostgreSQLConfig{
				Host:          "db.example.com",
				Port:          5433,
				User:          "admin",
				Password:      "secret",
				Name:          "production",
				SSLMode:       "verify-full",
				SSLRootCert:   "/certs/root.crt",
				SSLCert:       "/certs/client.crt",
				SSLKey:        "/certs/client.key",
				DefaultSchema: "app_schema",
				ConnOptions:   "application_name=authentik",
			},
			expected: "host=db.example.com port=5433 user=admin dbname=production password=secret sslmode=verify-full sslrootcert=/certs/root.crt sslcert=/certs/client.crt sslkey=/certs/client.key search_path=app_schema application_name=authentik",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := BuildDSN(tt.cfg)
			require.NoError(t, err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestPostgresStore_ConnectionPoolSettings(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	sqlDB, err := store.db.DB()
	require.NoError(t, err)

	// Verify connection pool is configured
	stats := sqlDB.Stats()
	assert.GreaterOrEqual(t, stats.MaxOpenConnections, 1, "Connection pool should be configured")

	// Test that we can create multiple sessions concurrently
	// This indirectly tests connection pool handling
	const numConcurrentOps = 20
	done := make(chan error, numConcurrentOps)

	for i := 0; i < numConcurrentOps; i++ {
		go func(id int) {
			req := httptest.NewRequest("GET", "/", nil)
			w := httptest.NewRecorder()

			session, err := store.New(req, "test_session")
			if err != nil {
				done <- err
				return
			}

			session.Values["test"] = id
			err = store.Save(req, w, session)
			done <- err
		}(i)
	}

	// Collect results
	for i := 0; i < numConcurrentOps; i++ {
		err := <-done
		assert.NoError(t, err, "Concurrent operation %d should succeed", i)
	}
}

// Helper function to create session data JSON
func createSessionData(t *testing.T, claims map[string]interface{}) string {
	sessionData := map[string]interface{}{
		constants.SessionClaims: claims,
		"_expires_at":           time.Now().Add(time.Hour).Format(time.RFC3339),
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)
	return string(sessionDataJSON)
}
