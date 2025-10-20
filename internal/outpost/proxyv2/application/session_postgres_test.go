package application

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	_ "gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/postgresstore"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func SetupTestDB(t *testing.T) (*gorm.DB, *postgresstore.RefreshableConnPool) {
	cfg := config.Get().PostgreSQL

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	}

	// Use standardized setup
	db, pool, err := postgresstore.SetupGORMWithRefreshablePool(cfg, gormConfig, 10, 100, time.Hour)
	require.NoError(t, err)

	return db, pool
}

func CleanupTestDB(t *testing.T, db *gorm.DB, pool *postgresstore.RefreshableConnPool) {
	assert.NoError(t, db.Exec("DELETE FROM authentik_providers_proxy_proxysession").Error)
	assert.NoError(t, pool.Close())
}

func NewTestStore(db *gorm.DB, pool *postgresstore.RefreshableConnPool) *postgresstore.PostgresStore {
	return postgresstore.NewTestStore(db, pool)
}

func TestPostgresStore_SessionLifecycle(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	// Create sessions directly in the database for testing
	userID := uuid.New()
	sessionKey := "test_session_" + uuid.New().String()

	sessionData := map[string]interface{}{
		constants.SessionClaims: map[string]interface{}{
			"sub":                userID.String(),
			"email":              "test@example.com",
			"preferred_username": "testuser",
			"custom_claim":       "custom_value",
			"groups":             []interface{}{"admin", "user"},
		},
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	session := postgresstore.ProxySession{
		UUID:        uuid.New(),
		SessionKey:  sessionKey,
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
		Expires:     time.Now().Add(time.Hour),
	}

	err = db.Create(&session).Error
	require.NoError(t, err)

	// Verify session was created
	var count int64
	db.Model(&postgresstore.ProxySession{}).Where("session_key = ?", sessionKey).Count(&count)
	assert.Equal(t, int64(1), count)

	// Verify session data
	var retrievedSession postgresstore.ProxySession
	err = db.First(&retrievedSession, "session_key = ?", sessionKey).Error
	require.NoError(t, err)

	assert.Equal(t, userID, *retrievedSession.UserID)

	// Parse session data
	var parsedData map[string]interface{}
	err = json.Unmarshal([]byte(retrievedSession.SessionData), &parsedData)
	require.NoError(t, err)

	claims, ok := parsedData[constants.SessionClaims].(map[string]interface{})
	assert.True(t, ok)
	assert.Equal(t, "test@example.com", claims["email"])
	assert.Equal(t, "testuser", claims["preferred_username"])
	assert.Equal(t, "custom_value", claims["custom_claim"])
}

func TestPostgresStore_LogoutSessions(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	// Create multiple sessions for different users
	user1 := uuid.New()
	user2 := uuid.New()

	createSessionData := func(userID uuid.UUID, email string) string {
		sessionData := map[string]interface{}{
			constants.SessionClaims: map[string]interface{}{
				"sub":   userID.String(),
				"email": email,
			},
		}
		sessionDataJSON, _ := json.Marshal(sessionData)
		return string(sessionDataJSON)
	}

	sessions := []postgresstore.ProxySession{
		{
			UUID:        uuid.New(),
			SessionKey:  "session_user1_1",
			UserID:      &user1,
			SessionData: createSessionData(user1, "user1@example.com"),
			Expires:     time.Now().Add(time.Hour),
		},
		{
			UUID:        uuid.New(),
			SessionKey:  "session_user1_2",
			UserID:      &user1,
			SessionData: createSessionData(user1, "user1@example.com"),
			Expires:     time.Now().Add(time.Hour),
		},
		{
			UUID:        uuid.New(),
			SessionKey:  "session_user2_1",
			UserID:      &user2,
			SessionData: createSessionData(user2, "user2@example.com"),
			Expires:     time.Now().Add(time.Hour),
		},
	}

	for _, session := range sessions {
		err := db.Create(&session).Error
		require.NoError(t, err)
	}

	// Verify all sessions were created
	var totalCount int64
	db.Model(&postgresstore.ProxySession{}).Count(&totalCount)
	assert.Equal(t, int64(3), totalCount)

	// Logout user1 sessions using LogoutSessions method
	store := NewTestStore(db, pool)
	err := store.LogoutSessions(context.Background(), func(c types.Claims) bool {
		return c.Sub == user1.String()
	})
	require.NoError(t, err)

	// Verify only user2 session remains
	var remainingCount int64
	db.Model(&postgresstore.ProxySession{}).Count(&remainingCount)
	assert.Equal(t, int64(1), remainingCount)

	var remainingSession postgresstore.ProxySession
	err = db.First(&remainingSession).Error
	require.NoError(t, err)
	assert.Equal(t, user2, *remainingSession.UserID)
}

func TestPostgresStore_SessionExpiration(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	// Create expired and valid sessions
	expiredSession := postgresstore.ProxySession{
		UUID:        uuid.New(),
		SessionKey:  "expired_session",
		SessionData: "{}",
		Expires:     time.Now().Add(-time.Hour),
	}
	validSession := postgresstore.ProxySession{
		UUID:        uuid.New(),
		SessionKey:  "valid_session",
		SessionData: "{}",
		Expires:     time.Now().Add(time.Hour),
	}

	err := db.Create(&expiredSession).Error
	require.NoError(t, err)
	err = db.Create(&validSession).Error
	require.NoError(t, err)

	// Clean up expired sessions (this is like what CleanupExpiredSessions would do)
	var sessions []postgresstore.ProxySession
	err = db.Find(&sessions).Error
	require.NoError(t, err)

	var expiredKeys []string
	now := time.Now()
	for _, session := range sessions {
		expTime := session.Expires
		if now.After(expTime) {
			expiredKeys = append(expiredKeys, session.SessionKey)
		}
	}

	result := db.Delete(&postgresstore.ProxySession{}, "session_key IN ?", expiredKeys)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(1), result.RowsAffected)

	// Verify only valid session remains
	var count int64
	db.Model(&postgresstore.ProxySession{}).Count(&count)
	assert.Equal(t, int64(1), count)

	var remaining postgresstore.ProxySession
	err = db.First(&remaining).Error
	require.NoError(t, err)
	assert.Equal(t, "valid_session", remaining.SessionKey)
}

func TestPostgresStore_SessionClaims(t *testing.T) {
	db, pool := SetupTestDB(t)
	defer CleanupTestDB(t, db, pool)

	// Create session with complex claims
	userID := uuid.New()
	sessionData := map[string]interface{}{
		constants.SessionClaims: map[string]interface{}{
			"sub":                userID.String(),
			"email":              "test@example.com",
			"preferred_username": "testuser",
			"groups":             []interface{}{"admin", "user"},
			"entitlements":       []interface{}{"read", "write"},
			"custom_field":       "custom_value",
		},
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	session := postgresstore.ProxySession{
		UUID:        uuid.New(),
		SessionKey:  "claims_test_session",
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
		Expires:     time.Now().Add(time.Hour),
	}

	err = db.Create(&session).Error
	require.NoError(t, err)

	// Retrieve and verify claims can be parsed
	var retrieved postgresstore.ProxySession
	err = db.First(&retrieved, "session_key = ?", "claims_test_session").Error
	require.NoError(t, err)

	assert.Equal(t, userID, *retrieved.UserID)

	// Parse and verify session data
	var parsedData map[string]interface{}
	err = json.Unmarshal([]byte(retrieved.SessionData), &parsedData)
	require.NoError(t, err)

	claims, ok := parsedData[constants.SessionClaims].(map[string]interface{})
	assert.True(t, ok)
	assert.Equal(t, "test@example.com", claims["email"])
	assert.Equal(t, "testuser", claims["preferred_username"])
	assert.Equal(t, "custom_value", claims["custom_field"])

	// Verify groups array
	groups, ok := claims["groups"].([]interface{})
	assert.True(t, ok)
	assert.Contains(t, groups, "admin")
	assert.Contains(t, groups, "user")

	// Verify entitlements array
	entitlements, ok := claims["entitlements"].([]interface{})
	assert.True(t, ok)
	assert.Contains(t, entitlements, "read")
	assert.Contains(t, entitlements, "write")
}
