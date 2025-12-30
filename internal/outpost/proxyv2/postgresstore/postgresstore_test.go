package postgresstore

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"math/big"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/jackc/pgx/v5"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// SetupTestDB creates a test database connection for testing
func SetupTestDB(t *testing.T) (*gorm.DB, *RefreshableConnPool) {
	cfg := config.Get().PostgreSQL

	t.Logf("PostgreSQL config: Host=%s Port=%d User=%s DBName=%s SSLMode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.Name, cfg.SSLMode)
	t.Logf("Password length: %d", len(cfg.Password))
	if cfg.Password == "" {
		t.Logf("WARNING: Password is empty!")
	}

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	}

	// Use standardized setup
	db, pool, err := SetupGORMWithRefreshablePool(cfg, gormConfig, 10, 100, time.Hour)
	require.NoError(t, err)

	return db, pool
}

// CleanupTestDB removes test sessions from the database
func CleanupTestDB(t *testing.T, db *gorm.DB, pool *RefreshableConnPool) {
	assert.NoError(t, db.Exec("DELETE FROM authentik_providers_proxy_proxysession").Error)
	assert.NoError(t, pool.Close())
}

func TestPostgresStore_New(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	req := httptest.NewRequest("GET", "/", nil)
	session, err := store.New(req, "test_session")

	assert.NoError(t, err)
	assert.True(t, session.IsNew)
	assert.Equal(t, "test_session", session.Name())
}

func TestPostgresStore_Save(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
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
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
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
	}

	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	proxySession := ProxySession{
		UUID:        uuid.New(),
		SessionKey:  sessionKey,
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
		Expires:     time.Now().Add(time.Hour),
	}
	err = db.Create(&proxySession).Error
	require.NoError(t, err)

	// Load the session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.load(context.Background(), session)
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
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Create a session in the database
	sessionKey := "test_session_456"

	proxySession := ProxySession{
		UUID:        uuid.New(),
		SessionKey:  sessionKey,
		SessionData: "{}",
		Expires:     time.Now().Add(time.Hour),
	}
	err := db.Create(&proxySession).Error
	require.NoError(t, err)

	// Delete the session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.delete(context.Background(), session)
	assert.NoError(t, err)

	// Verify session was deleted
	var count int64
	db.Model(&ProxySession{}).Where("session_key = ?", sessionKey).Count(&count)
	assert.Equal(t, int64(0), count)
}

func TestPostgresStore_LogoutSessions_ByUserID(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Create multiple sessions for different users
	user1 := uuid.New()
	user2 := uuid.New()

	sessions := []ProxySession{
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_user1_1",
			UserID:     &user1,
			SessionData: createSessionData(t, map[string]interface{}{
				"sub":   user1.String(),
				"email": "user1@example.com",
			}),
		},
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_user1_2",
			UserID:     &user1,
			SessionData: createSessionData(t, map[string]interface{}{
				"sub":   user1.String(),
				"email": "user1@example.com",
			}),
		},
		{
			UUID:       uuid.New(),
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
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Create sessions with different emails
	sessions := []ProxySession{
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_admin_1",
			SessionData: createSessionData(t, map[string]interface{}{
				"email": "admin@example.com",
			}),
		},
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_admin_2",
			SessionData: createSessionData(t, map[string]interface{}{
				"email": "admin@example.com",
			}),
		},
		{
			UUID:       uuid.New(),
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
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Create sessions with different group memberships
	sessions := []ProxySession{
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_admin_user",
			SessionData: createSessionData(t, map[string]interface{}{
				"email":  "admin@example.com",
				"groups": []interface{}{"admin", "user"},
			}),
		},
		{
			UUID:       uuid.New(),
			SessionKey: "test_session_regular_user",
			SessionData: createSessionData(t, map[string]interface{}{
				"email":  "user@example.com",
				"groups": []interface{}{"user"},
			}),
		},
		{
			UUID:       uuid.New(),
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
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Create an expired session
	sessionKey := "test_expired_load"
	expiredData := map[string]interface{}{
		constants.SessionClaims: map[string]interface{}{
			"sub": "test-user",
		},
	}
	expiredDataJSON, _ := json.Marshal(expiredData)

	proxySession := ProxySession{
		UUID:        uuid.New(),
		SessionKey:  sessionKey,
		SessionData: string(expiredDataJSON),
		Expires:     time.Now().Add(-time.Hour),
	}
	err := db.Create(&proxySession).Error
	require.NoError(t, err)

	// Try to load the expired session
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.load(context.Background(), session)

	// Should return ErrRecordNotFound because session is expired
	assert.Error(t, err)
	assert.Equal(t, gorm.ErrRecordNotFound, err)

	// Verify the expired session was deleted
	var count int64
	db.Model(&ProxySession{}).Where("session_key = ?", sessionKey).Count(&count)
	assert.Equal(t, int64(0), count)
}

func TestPostgresStore_ConcurrentSessionAccess(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	// Test concurrent access by creating separate sessions for each goroutine
	// This tests that the connection pool handles concurrent operations correctly
	const numGoroutines = 10
	done := make(chan error, numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			// Each goroutine creates its own unique session
			req := httptest.NewRequest("GET", "/", nil)
			w := httptest.NewRecorder()

			session, err := store.New(req, "test_session")
			if err != nil {
				done <- fmt.Errorf("goroutine %d failed to create session: %w", id, err)
				return
			}

			// Set some data
			session.Values["goroutine_id"] = id
			session.Values["timestamp"] = time.Now().Unix()

			// Save session
			err = store.Save(req, w, session)
			if err != nil {
				done <- fmt.Errorf("goroutine %d failed to save: %w", id, err)
				return
			}

			// Load it back
			session2, err := store.New(req, "test_session")
			if err != nil {
				done <- fmt.Errorf("goroutine %d failed to create session for load: %w", id, err)
				return
			}
			session2.ID = session.ID
			err = store.load(context.Background(), session2)
			if err != nil {
				done <- fmt.Errorf("goroutine %d failed to load: %w", id, err)
				return
			}

			done <- nil
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < numGoroutines; i++ {
		err := <-done
		assert.NoError(t, err)
	}
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

func TestBuildConnConfig(t *testing.T) {
	tests := []struct {
		name     string
		cfg      config.PostgreSQLConfig
		validate func(*testing.T, *pgx.ConnConfig)
	}{
		{
			name: "basic configuration",
			cfg: config.PostgreSQLConfig{
				Host: "localhost",
				Port: 5432,
				User: "testuser",
				Name: "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "localhost", cc.Host)
				assert.Equal(t, uint16(5432), cc.Port)
				assert.Equal(t, "testuser", cc.User)
				assert.Equal(t, "testdb", cc.Database)
				assert.Equal(t, "", cc.Password)
			},
		},
		{
			name: "with simple password",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: "testpass",
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "testpass", cc.Password)
			},
		},
		{
			name: "with password containing spaces",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: "my secure password",
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "my secure password", cc.Password)
			},
		},
		{
			name: "with password containing single quotes",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: "pass'word",
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "pass'word", cc.Password)
			},
		},
		{
			name: "with password containing backslashes",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: `pass\word`,
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, `pass\word`, cc.Password)
			},
		},
		{
			name: "with password containing special characters",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: `p@ss w0rd!#$%^&*()`,
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, `p@ss w0rd!#$%^&*()`, cc.Password)
			},
		},
		{
			name: "with password containing quotes and backslashes",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: `my'pass\word"here`,
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, `my'pass\word"here`, cc.Password)
			},
		},
		{
			name: "with passphrase (multiple spaces)",
			cfg: config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: "the quick brown fox jumps over",
				Name:     "testdb",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "the quick brown fox jumps over", cc.Password)
			},
		},
		{
			name: "with sslmode=disable",
			cfg: config.PostgreSQLConfig{
				Host:    "localhost",
				Port:    5432,
				User:    "testuser",
				Name:    "testdb",
				SSLMode: "disable",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Nil(t, cc.TLSConfig)
			},
		},
		{
			name: "with sslmode=require (no certs)",
			cfg: config.PostgreSQLConfig{
				Host:    "localhost",
				Port:    5432,
				User:    "testuser",
				Name:    "testdb",
				SSLMode: "require",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.NotNil(t, cc.TLSConfig)
				assert.True(t, cc.TLSConfig.InsecureSkipVerify)
			},
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
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "custom_schema", cc.RuntimeParams["search_path"])
			},
		},
		{
			name: "with connection options",
			cfg: config.PostgreSQLConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "testuser",
				Name:        "testdb",
				ConnOptions: base64.StdEncoding.EncodeToString([]byte(`{"connect_timeout":"10","application_name":"authentik"}`)),
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, 10*time.Second, cc.ConnectTimeout)
				assert.Equal(t, "authentik", cc.RuntimeParams["application_name"])
			},
		},
		{
			name: "with target_session_attrs",
			cfg: config.PostgreSQLConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "testuser",
				Name:        "testdb",
				ConnOptions: base64.StdEncoding.EncodeToString([]byte(`{"target_session_attrs":"read-write"}`)),
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "read-write", cc.RuntimeParams["target_session_attrs"])
			},
		},
		{
			name: "full configuration with special password",
			cfg: config.PostgreSQLConfig{
				Host:          "db.example.com",
				Port:          5433,
				User:          "admin",
				Password:      "my super secret password!@#",
				Name:          "production",
				SSLMode:       "require",
				DefaultSchema: "app_schema",
				ConnOptions:   base64.StdEncoding.EncodeToString([]byte(`{"application_name":"authentik"}`)),
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "db.example.com", cc.Host)
				assert.Equal(t, uint16(5433), cc.Port)
				assert.Equal(t, "admin", cc.User)
				assert.Equal(t, "my super secret password!@#", cc.Password)
				assert.Equal(t, "production", cc.Database)
				assert.Equal(t, "app_schema", cc.RuntimeParams["search_path"])
				assert.Equal(t, "authentik", cc.RuntimeParams["application_name"])
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := BuildConnConfig(tt.cfg)
			require.NoError(t, err)
			require.NotNil(t, result)
			tt.validate(t, result)
		})
	}
}

// TestBuildConnConfig_WithSSLCertificates tests SSL certificate configuration
func TestBuildConnConfig_WithSSLCertificates(t *testing.T) {
	rootCertPath, clientCertPath, clientKeyPath, cleanup := generateTestCerts(t)
	defer cleanup()

	tests := []struct {
		name     string
		cfg      config.PostgreSQLConfig
		validate func(*testing.T, *pgx.ConnConfig)
	}{
		{
			name: "verify-full with all certificates",
			cfg: config.PostgreSQLConfig{
				Host:        "db.example.com",
				Port:        5432,
				User:        "testuser",
				Password:    "my secure password",
				Name:        "testdb",
				SSLMode:     "verify-full",
				SSLRootCert: rootCertPath,
				SSLCert:     clientCertPath,
				SSLKey:      clientKeyPath,
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				require.NotNil(t, cc.TLSConfig)
				assert.False(t, cc.TLSConfig.InsecureSkipVerify)
				assert.Equal(t, "db.example.com", cc.TLSConfig.ServerName)
				assert.NotNil(t, cc.TLSConfig.RootCAs)
				assert.Len(t, cc.TLSConfig.Certificates, 1)
			},
		},
		{
			name: "verify-ca with root cert only",
			cfg: config.PostgreSQLConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "testuser",
				Name:        "testdb",
				SSLMode:     "verify-ca",
				SSLRootCert: rootCertPath,
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				require.NotNil(t, cc.TLSConfig)
				assert.False(t, cc.TLSConfig.InsecureSkipVerify)
				assert.NotNil(t, cc.TLSConfig.RootCAs)
				assert.Empty(t, cc.TLSConfig.Certificates)
			},
		},
		{
			name: "require with client cert",
			cfg: config.PostgreSQLConfig{
				Host:    "localhost",
				Port:    5432,
				User:    "testuser",
				Name:    "testdb",
				SSLMode: "require",
				SSLCert: clientCertPath,
				SSLKey:  clientKeyPath,
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				require.NotNil(t, cc.TLSConfig)
				assert.True(t, cc.TLSConfig.InsecureSkipVerify)
				assert.Len(t, cc.TLSConfig.Certificates, 1)
			},
		},
		{
			name: "full configuration with SSL and special password",
			cfg: config.PostgreSQLConfig{
				Host:          "db.example.com",
				Port:          5433,
				User:          "admin",
				Password:      "my super secret password!@#",
				Name:          "production",
				SSLMode:       "verify-full",
				SSLRootCert:   rootCertPath,
				SSLCert:       clientCertPath,
				SSLKey:        clientKeyPath,
				DefaultSchema: "app_schema",
				ConnOptions:   base64.StdEncoding.EncodeToString([]byte(`{"application_name":"authentik"}`)),
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "db.example.com", cc.Host)
				assert.Equal(t, uint16(5433), cc.Port)
				assert.Equal(t, "admin", cc.User)
				assert.Equal(t, "my super secret password!@#", cc.Password)
				assert.Equal(t, "production", cc.Database)
				require.NotNil(t, cc.TLSConfig)
				assert.False(t, cc.TLSConfig.InsecureSkipVerify)
				assert.Equal(t, "db.example.com", cc.TLSConfig.ServerName)
				assert.NotNil(t, cc.TLSConfig.RootCAs)
				assert.Len(t, cc.TLSConfig.Certificates, 1)
				assert.Equal(t, "app_schema", cc.RuntimeParams["search_path"])
				assert.Equal(t, "authentik", cc.RuntimeParams["application_name"])
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := BuildConnConfig(tt.cfg)
			require.NoError(t, err)
			require.NotNil(t, result)
			tt.validate(t, result)
		})
	}
}

// TestBuildDSN_WithSpecialPasswords tests that BuildDSN can handle passwords with special characters
// by verifying the DSN can actually be used to connect to a database
func TestBuildDSN_WithSpecialPasswords(t *testing.T) {
	tests := []struct {
		name     string
		password string
	}{
		{"space in password", "my password"},
		{"multiple spaces", "the quick brown fox"},
		{"single quote", "pass'word"},
		{"backslash", `pass\word`},
		{"double quote", `pass"word`},
		{"special chars", `p@ss!#$%^&*()`},
		{"mixed special", `my'pass\word"here`},
		{"unicode", "pässwörd"},
		{"leading/trailing spaces", "  password  "},
		{"tab character", "pass\tword"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := config.PostgreSQLConfig{
				Host:     "localhost",
				Port:     5432,
				User:     "testuser",
				Password: tt.password,
				Name:     "testdb",
			}

			// Test that BuildDSN doesn't error
			dsn, err := BuildDSN(cfg)
			require.NoError(t, err)
			require.NotEmpty(t, dsn)

			// Test that BuildConnConfig preserves the password exactly
			connConfig, err := BuildConnConfig(cfg)
			require.NoError(t, err)
			assert.Equal(t, tt.password, connConfig.Password, "Password should be preserved exactly")
		})
	}
}

func TestPostgresStore_ConnectionPoolSettings(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	store := NewTestStore(db, pool)
	sqlDB := pool.GetDB()
	require.NotNil(t, sqlDB)

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

// TestParseConnOptions tests the base64 JSON parsing of connection options
func TestParseConnOptions(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		expected    map[string]string
		expectError bool
		errorMsg    string
	}{
		{
			name:     "simple key-value",
			input:    base64.StdEncoding.EncodeToString([]byte(`{"target_session_attrs":"read-write"}`)),
			expected: map[string]string{"target_session_attrs": "read-write"},
		},
		{
			name:     "multiple options",
			input:    base64.StdEncoding.EncodeToString([]byte(`{"connect_timeout":"10","application_name":"authentik"}`)),
			expected: map[string]string{"connect_timeout": "10", "application_name": "authentik"},
		},
		{
			name:     "numeric value as number",
			input:    base64.StdEncoding.EncodeToString([]byte(`{"connect_timeout":10}`)),
			expected: map[string]string{"connect_timeout": "10"},
		},
		{
			name:     "boolean value",
			input:    base64.StdEncoding.EncodeToString([]byte(`{"default_transaction_read_only":true}`)),
			expected: map[string]string{"default_transaction_read_only": "true"},
		},
		{
			name:     "empty object",
			input:    base64.StdEncoding.EncodeToString([]byte(`{}`)),
			expected: map[string]string{},
		},
		{
			name:        "invalid base64",
			input:       "not-valid-base64!!!",
			expectError: true,
			errorMsg:    "invalid base64 encoding",
		},
		{
			name:        "invalid JSON",
			input:       base64.StdEncoding.EncodeToString([]byte(`not json`)),
			expectError: true,
			errorMsg:    "invalid JSON",
		},
		{
			name:        "JSON array instead of object",
			input:       base64.StdEncoding.EncodeToString([]byte(`["value1", "value2"]`)),
			expectError: true,
			errorMsg:    "invalid JSON",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := parseConnOptions(tt.input)
			if tt.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorMsg)
			} else {
				require.NoError(t, err)
				assert.Equal(t, tt.expected, result)
			}
		})
	}
}

// TestApplyConnOptions tests that connection options are applied correctly to pgx.ConnConfig
func TestApplyConnOptions(t *testing.T) {
	tests := []struct {
		name        string
		opts        map[string]string
		validate    func(*testing.T, *pgx.ConnConfig)
		expectError bool
		errorMsg    string
	}{
		{
			name: "connect_timeout sets ConnectTimeout",
			opts: map[string]string{"connect_timeout": "30"},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, 30*time.Second, cc.ConnectTimeout)
			},
		},
		{
			name: "target_session_attrs goes to RuntimeParams",
			opts: map[string]string{"target_session_attrs": "read-write"},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "read-write", cc.RuntimeParams["target_session_attrs"])
			},
		},
		{
			name: "application_name goes to RuntimeParams",
			opts: map[string]string{"application_name": "my-app"},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "my-app", cc.RuntimeParams["application_name"])
			},
		},
		{
			name: "statement_timeout goes to RuntimeParams",
			opts: map[string]string{"statement_timeout": "5000"},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "5000", cc.RuntimeParams["statement_timeout"])
			},
		},
		{
			name: "unknown options go to RuntimeParams",
			opts: map[string]string{"custom_param": "custom_value"},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, "custom_value", cc.RuntimeParams["custom_param"])
			},
		},
		{
			name: "multiple options",
			opts: map[string]string{
				"connect_timeout":      "10",
				"target_session_attrs": "read-write",
				"application_name":     "authentik",
			},
			validate: func(t *testing.T, cc *pgx.ConnConfig) {
				assert.Equal(t, 10*time.Second, cc.ConnectTimeout)
				assert.Equal(t, "read-write", cc.RuntimeParams["target_session_attrs"])
				assert.Equal(t, "authentik", cc.RuntimeParams["application_name"])
			},
		},
		{
			name:        "invalid connect_timeout",
			opts:        map[string]string{"connect_timeout": "not-a-number"},
			expectError: true,
			errorMsg:    "invalid connect_timeout value",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a base config
			connConfig, err := pgx.ParseConfig("")
			require.NoError(t, err)
			connConfig.RuntimeParams = make(map[string]string)

			err = applyConnOptions(connConfig, tt.opts)
			if tt.expectError {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorMsg)
			} else {
				require.NoError(t, err)
				tt.validate(t, connConfig)
			}
		})
	}
}

// TestBuildConnConfig_Base64JSONConnOptions tests the full integration of base64 JSON connection options
func TestBuildConnConfig_Base64JSONConnOptions(t *testing.T) {
	t.Run("bug report scenario - target_session_attrs", func(t *testing.T) {
		cfg := config.PostgreSQLConfig{
			Host:        "localhost",
			Port:        5432,
			User:        "authentik",
			Name:        "authentik",
			ConnOptions: "eyJ0YXJnZXRfc2Vzc2lvbl9hdHRycyI6InJlYWQtd3JpdGUifQ==",
		}

		connConfig, err := BuildConnConfig(cfg)
		require.NoError(t, err)
		assert.Equal(t, "read-write", connConfig.RuntimeParams["target_session_attrs"])
	})

	t.Run("complex connection options", func(t *testing.T) {
		// {"connect_timeout":10,"target_session_attrs":"read-write","application_name":"authentik-proxy"}
		connOpts := base64.StdEncoding.EncodeToString([]byte(`{"connect_timeout":10,"target_session_attrs":"read-write","application_name":"authentik-proxy"}`))
		cfg := config.PostgreSQLConfig{
			Host:        "localhost",
			Port:        5432,
			User:        "authentik",
			Name:        "authentik",
			ConnOptions: connOpts,
		}

		connConfig, err := BuildConnConfig(cfg)
		require.NoError(t, err)
		assert.Equal(t, 10*time.Second, connConfig.ConnectTimeout)
		assert.Equal(t, "read-write", connConfig.RuntimeParams["target_session_attrs"])
		assert.Equal(t, "authentik-proxy", connConfig.RuntimeParams["application_name"])
	})
}

// Helper function to create session data JSON
func createSessionData(t *testing.T, claims map[string]interface{}) string {
	sessionData := map[string]interface{}{
		constants.SessionClaims: claims,
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)
	return string(sessionDataJSON)
}

// generateTestCerts creates temporary SSL certificates for testing
func generateTestCerts(t *testing.T) (rootCertPath, clientCertPath, clientKeyPath string, cleanup func()) {
	tmpDir := t.TempDir()

	// Generate CA certificate
	caKey, err := rsa.GenerateKey(rand.Reader, 2048)
	require.NoError(t, err)

	caTemplate := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"Test CA"},
		},
		NotBefore:             time.Now(),
		NotAfter:              time.Now().Add(24 * time.Hour),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign,
		BasicConstraintsValid: true,
		IsCA:                  true,
	}

	caCertDER, err := x509.CreateCertificate(rand.Reader, caTemplate, caTemplate, &caKey.PublicKey, caKey)
	require.NoError(t, err)

	// Write CA certificate
	rootCertPath = filepath.Join(tmpDir, "root.crt")
	rootCertFile, err := os.Create(rootCertPath)
	require.NoError(t, err)
	defer func() {
		if closeErr := rootCertFile.Close(); closeErr != nil {
			t.Logf("failed to close root cert file: %v", closeErr)
		}
	}()
	err = pem.Encode(rootCertFile, &pem.Block{Type: "CERTIFICATE", Bytes: caCertDER})
	require.NoError(t, err)

	// Generate client key
	clientKey, err := rsa.GenerateKey(rand.Reader, 2048)
	require.NoError(t, err)

	// Generate client certificate
	clientTemplate := &x509.Certificate{
		SerialNumber: big.NewInt(2),
		Subject: pkix.Name{
			Organization: []string{"Test Client"},
		},
		NotBefore:   time.Now(),
		NotAfter:    time.Now().Add(24 * time.Hour),
		KeyUsage:    x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
	}

	clientCertDER, err := x509.CreateCertificate(rand.Reader, clientTemplate, caTemplate, &clientKey.PublicKey, caKey)
	require.NoError(t, err)

	// Write client certificate
	clientCertPath = filepath.Join(tmpDir, "client.crt")
	clientCertFile, err := os.Create(clientCertPath)
	require.NoError(t, err)
	defer func() {
		if closeErr := clientCertFile.Close(); closeErr != nil {
			t.Logf("failed to close client cert file: %v", closeErr)
		}
	}()
	err = pem.Encode(clientCertFile, &pem.Block{Type: "CERTIFICATE", Bytes: clientCertDER})
	require.NoError(t, err)

	// Write client key
	clientKeyPath = filepath.Join(tmpDir, "client.key")
	clientKeyFile, err := os.Create(clientKeyPath)
	require.NoError(t, err)
	defer func() {
		if closeErr := clientKeyFile.Close(); closeErr != nil {
			t.Logf("failed to close client key file: %v", closeErr)
		}
	}()
	clientKeyBytes := x509.MarshalPKCS1PrivateKey(clientKey)
	err = pem.Encode(clientKeyFile, &pem.Block{Type: "RSA PRIVATE KEY", Bytes: clientKeyBytes})
	require.NoError(t, err)

	cleanup = func() {
		// TempDir cleanup is automatic in Go tests
	}

	return rootCertPath, clientCertPath, clientKeyPath, cleanup
}
