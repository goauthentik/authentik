package application

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"

	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/postgresstore"
)

func TestPostgresStore_SessionLifecycle(t *testing.T) {

	// Create test database
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

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

	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

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
		err = db.Create(&session).Error
		require.NoError(t, err)
	}

	// Verify all sessions were created
	var totalCount int64
	db.Model(&postgresstore.ProxySession{}).Count(&totalCount)
	assert.Equal(t, int64(3), totalCount)

	// Simulate logout of user1 sessions by deleting them directly
	// todo(dominic): should probably use LogoutSessions method instead to really test this
	result := db.Delete(&postgresstore.ProxySession{}, "user_id = ?", user1)
	require.NoError(t, result.Error)
	assert.Equal(t, int64(2), result.RowsAffected)

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

	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

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

	err = db.Create(&expiredSession).Error
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

	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

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
