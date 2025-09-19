package application

import (
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"

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

	session := postgresstore.ProxySession{
		SessionKey:   sessionKey,
		UserID:       &userID,
		UserEmail:    "test@example.com",
		UserUsername: "testuser",
		AccessToken:  "access_token_123",
		RefreshToken: "refresh_token_123",
		IDToken:      "id_token_123",
		ExpiresAt:    time.Now().Add(time.Hour),
		ExtraClaims:  `{"custom_claim":"custom_value","groups":["admin","user"]}`,
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
	assert.Equal(t, "test@example.com", retrievedSession.UserEmail)
	assert.Equal(t, "testuser", retrievedSession.UserUsername)
	assert.Contains(t, retrievedSession.ExtraClaims, "custom_claim")
}

func TestPostgresStore_LogoutSessions(t *testing.T) {

	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	require.NoError(t, err)

	err = db.AutoMigrate(&postgresstore.ProxySession{})
	require.NoError(t, err)

	// Create multiple sessions for different users
	user1 := uuid.New()
	user2 := uuid.New()

	sessions := []postgresstore.ProxySession{
		{
			SessionKey: "session_user1_1",
			UserID:     &user1,
			UserEmail:  "user1@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
		},
		{
			SessionKey: "session_user1_2",
			UserID:     &user1,
			UserEmail:  "user1@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
		},
		{
			SessionKey: "session_user2_1",
			UserID:     &user2,
			UserEmail:  "user2@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
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

	// Create expired and valid sessions
	expiredSession := postgresstore.ProxySession{
		SessionKey: "expired_session",
		ExpiresAt:  time.Now().Add(-time.Hour), // Expired 1 hour ago
	}
	validSession := postgresstore.ProxySession{
		SessionKey: "valid_session",
		ExpiresAt:  time.Now().Add(time.Hour), // Expires in 1 hour
	}

	err = db.Create(&expiredSession).Error
	require.NoError(t, err)
	err = db.Create(&validSession).Error
	require.NoError(t, err)

	// Clean up expired sessions
	result := db.Delete(&postgresstore.ProxySession{}, "expires_at <= ?", time.Now())
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
	session := postgresstore.ProxySession{
		SessionKey:   "claims_test_session",
		UserID:       &userID,
		UserEmail:    "test@example.com",
		UserUsername: "testuser",
		ExpiresAt:    time.Now().Add(time.Hour),
		ExtraClaims:  `{"groups":["admin","user"],"entitlements":["read","write"],"custom_field":"custom_value"}`,
	}

	err = db.Create(&session).Error
	require.NoError(t, err)

	// Retrieve and verify claims can be parsed
	var retrieved postgresstore.ProxySession
	err = db.First(&retrieved, "session_key = ?", "claims_test_session").Error
	require.NoError(t, err)

	assert.Equal(t, userID, *retrieved.UserID)
	assert.Equal(t, "test@example.com", retrieved.UserEmail)
	assert.Equal(t, "testuser", retrieved.UserUsername)
	assert.Contains(t, retrieved.ExtraClaims, "groups")
	assert.Contains(t, retrieved.ExtraClaims, "admin")
	assert.Contains(t, retrieved.ExtraClaims, "custom_field")
}
