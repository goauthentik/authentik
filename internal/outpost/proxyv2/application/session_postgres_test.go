package application

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/postgresstore"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func SetupTestDB(t *testing.T) *gorm.DB {
	cfg := config.Get().PostgreSQL
	dsn := buildDSN(cfg)

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	}

	db, err := gorm.Open(postgres.Open(dsn), gormConfig)
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

	return db
}

func CleanupTestDB(t *testing.T, db *gorm.DB) {
	db.Exec("DELETE FROM authentik_outposts_proxy_session")
}

func buildDSN(cfg config.PostgreSQLConfig) string {
	dsn, err := postgresstore.BuildDSN(cfg)
	if err != nil {
		panic(err)
	}
	return dsn
}

func NewTestStore(db *gorm.DB) *postgresstore.PostgresStore {
	return postgresstore.NewTestStore(db)
}

func TestPostgresStore_SessionLifecycle(t *testing.T) {
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

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
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	session := postgresstore.ProxySession{
		SessionKey:  sessionKey,
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
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
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	// Create multiple sessions for different users
	user1 := uuid.New()
	user2 := uuid.New()

	createSessionData := func(userID uuid.UUID, email string) string {
		sessionData := map[string]interface{}{
			constants.SessionClaims: map[string]interface{}{
				"sub":   userID.String(),
				"email": email,
			},
			"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
		}
		sessionDataJSON, _ := json.Marshal(sessionData)
		return string(sessionDataJSON)
	}

	sessions := []postgresstore.ProxySession{
		{
			SessionKey:  "session_user1_1",
			UserID:      &user1,
			SessionData: createSessionData(user1, "user1@example.com"),
		},
		{
			SessionKey:  "session_user1_2",
			UserID:      &user1,
			SessionData: createSessionData(user1, "user1@example.com"),
		},
		{
			SessionKey:  "session_user2_1",
			UserID:      &user2,
			SessionData: createSessionData(user2, "user2@example.com"),
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
	store := NewTestStore(db)
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
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

	createSessionDataWithExpiry := func(expiresAt time.Time) string {
		sessionData := map[string]interface{}{
			"_expires_at": expiresAt.Format(time.RFC3339),
		}
		sessionDataJSON, _ := json.Marshal(sessionData)
		return string(sessionDataJSON)
	}

	// Create expired and valid sessions
	expiredSession := postgresstore.ProxySession{
		SessionKey:  "expired_session",
		SessionData: createSessionDataWithExpiry(time.Now().Add(-time.Hour)),
	}
	validSession := postgresstore.ProxySession{
		SessionKey:  "valid_session",
		SessionData: createSessionDataWithExpiry(time.Now().Add(time.Hour)),
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
		var sessionData map[string]interface{}
		if err := json.Unmarshal([]byte(session.SessionData), &sessionData); err == nil {
			if expiresAt, ok := sessionData["_expires_at"].(string); ok {
				if expTime, err := time.Parse(time.RFC3339, expiresAt); err == nil {
					if now.After(expTime) {
						expiredKeys = append(expiredKeys, session.SessionKey)
					}
				}
			}
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
	db := SetupTestDB(t)
	defer CleanupTestDB(t, db)

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
		"_expires_at": time.Now().Add(time.Hour).Format(time.RFC3339),
	}
	sessionDataJSON, err := json.Marshal(sessionData)
	require.NoError(t, err)

	session := postgresstore.ProxySession{
		SessionKey:  "claims_test_session",
		UserID:      &userID,
		SessionData: string(sessionDataJSON),
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
