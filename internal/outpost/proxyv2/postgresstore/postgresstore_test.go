package postgresstore

import (
	"context"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"

	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func setupTestDB() (*gorm.DB, error) {
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	// Auto-migrate the schema
	err = db.AutoMigrate(&ProxySession{})
	if err != nil {
		return nil, err
	}

	return db, nil
}

func TestPostgresStore_New(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
	db, err := setupTestDB()
	require.NoError(t, err)

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
		"access_token":       "access_token_123",
		"refresh_token":      "refresh_token_123",
		"id_token":           "id_token_123",
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
	assert.Equal(t, "test@example.com", savedSession.UserEmail)
	assert.Equal(t, "testuser", savedSession.UserUsername)
	assert.Equal(t, "access_token_123", savedSession.AccessToken)
	assert.Contains(t, savedSession.ExtraClaims, "custom_claim")
}

func TestPostgresStore_Load(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
	proxySession := ProxySession{
		SessionKey:   sessionKey,
		UserID:       &userID,
		UserEmail:    "test@example.com",
		UserUsername: "testuser",
		AccessToken:  "access_token_123",
		RefreshToken: "refresh_token_123",
		IDToken:      "id_token_123",
		ExpiresAt:    time.Now().Add(time.Hour),
		ExtraClaims:  `{"custom_claim":"custom_value"}`,
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
	assert.Equal(t, "access_token_123", claims["access_token"])
	assert.Equal(t, "custom_value", claims["custom_claim"])
}

func TestPostgresStore_Delete(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
	proxySession := ProxySession{
		SessionKey: sessionKey,
		ExpiresAt:  time.Now().Add(time.Hour),
	}
	err = db.Create(&proxySession).Error
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
	db, err := setupTestDB()
	require.NoError(t, err)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create expired and valid sessions
	expiredSession := ProxySession{
		SessionKey: "expired_session",
		ExpiresAt:  time.Now().Add(-time.Hour), // Expired 1 hour ago
	}
	validSession := ProxySession{
		SessionKey: "valid_session",
		ExpiresAt:  time.Now().Add(time.Hour), // Expires in 1 hour
	}

	err = db.Create(&expiredSession).Error
	require.NoError(t, err)
	err = db.Create(&validSession).Error
	require.NoError(t, err)

	// Clean up expired sessions
	err = store.CleanupExpired()
	assert.NoError(t, err)

	// Verify only valid session remains
	var count int64
	db.Model(&ProxySession{}).Count(&count)
	assert.Equal(t, int64(1), count)

	var remaining ProxySession
	err = db.First(&remaining).Error
	assert.NoError(t, err)
	assert.Equal(t, "valid_session", remaining.SessionKey)
}

func TestPostgresStore_LogoutSessions_Integration(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
			SessionKey:   "session_user1_1",
			UserID:       &user1,
			UserEmail:    "user1@example.com",
			UserUsername: "user1",
			ExpiresAt:    time.Now().Add(time.Hour),
			ExtraClaims:  `{"groups":["admin"],"role":"admin"}`,
		},
		{
			SessionKey:   "session_user1_2", 
			UserID:       &user1,
			UserEmail:    "user1@example.com",
			UserUsername: "user1",
			ExpiresAt:    time.Now().Add(time.Hour),
			ExtraClaims:  `{"groups":["admin"],"role":"admin"}`,
		},
		{
			SessionKey:   "session_user2_1",
			UserID:       &user2, 
			UserEmail:    "user2@example.com",
			UserUsername: "user2",
			ExpiresAt:    time.Now().Add(time.Hour),
			ExtraClaims:  `{"groups":["user"],"role":"user"}`,
		},
	}
	
	for _, session := range sessions {
		err = db.Create(&session).Error
		require.NoError(t, err)
	}
	
	// Test filtering by user ID
	ctx := context.Background()
	err = store.LogoutSessions(ctx, func(c types.Claims) bool {
		return c.Sub == user1.String()
	})
	assert.NoError(t, err)
	
	// Verify only user2 session remains
	var count int64
	db.Model(&ProxySession{}).Count(&count)
	assert.Equal(t, int64(1), count)
	
	var remaining ProxySession
	err = db.First(&remaining).Error
	assert.NoError(t, err)
	assert.Equal(t, user2, *remaining.UserID)
}

func TestPostgresStore_LogoutSessions_ByEmail(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
			SessionKey: "session_admin_1",
			UserEmail:  "admin@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
		},
		{
			SessionKey: "session_admin_2",
			UserEmail:  "admin@example.com", 
			ExpiresAt:  time.Now().Add(time.Hour),
		},
		{
			SessionKey: "session_user_1",
			UserEmail:  "user@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
		},
	}
	
	for _, session := range sessions {
		err = db.Create(&session).Error
		require.NoError(t, err)
	}
	
	// Logout all admin sessions
	ctx := context.Background()
	err = store.LogoutSessions(ctx, func(c types.Claims) bool {
		return c.Email == "admin@example.com"
	})
	assert.NoError(t, err)
	
	// Verify only user session remains
	var count int64
	db.Model(&ProxySession{}).Count(&count)
	assert.Equal(t, int64(1), count)
	
	var remaining ProxySession
	err = db.First(&remaining).Error
	assert.NoError(t, err)
	assert.Equal(t, "user@example.com", remaining.UserEmail)
}

func TestPostgresStore_LogoutSessions_WithGroups(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

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
			SessionKey: "session_admin_user",
			UserEmail:  "admin@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
			ExtraClaims: `{"groups":["admin","user"]}`,
		},
		{
			SessionKey: "session_regular_user",
			UserEmail:  "user@example.com", 
			ExpiresAt:  time.Now().Add(time.Hour),
			ExtraClaims: `{"groups":["user"]}`,
		},
		{
			SessionKey: "session_guest",
			UserEmail:  "guest@example.com",
			ExpiresAt:  time.Now().Add(time.Hour),
			ExtraClaims: `{"groups":["guest"]}`,
		},
	}
	
	for _, session := range sessions {
		err = db.Create(&session).Error
		require.NoError(t, err)
	}
	
	// Logout all sessions that have "admin" group
	ctx := context.Background()
	err = store.LogoutSessions(ctx, func(c types.Claims) bool {
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
	db.Model(&ProxySession{}).Count(&count)
	assert.Equal(t, int64(2), count)
	
	// Verify remaining sessions don't have admin group
	var remainingSessions []ProxySession
	err = db.Find(&remainingSessions).Error
	assert.NoError(t, err)
	
	for _, session := range remainingSessions {
		assert.NotEqual(t, "admin@example.com", session.UserEmail)
	}
}

func TestPostgresStore_LastAccessed_Update(t *testing.T) {
	db, err := setupTestDB()
	require.NoError(t, err)

	store := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
	}

	// Create a session
	sessionKey := "test_session_123"
	originalTime := time.Now().Add(-time.Hour)
	
	proxySession := ProxySession{
		SessionKey:   sessionKey,
		UserEmail:    "test@example.com",
		ExpiresAt:    time.Now().Add(time.Hour),
		LastAccessed: originalTime,
	}
	err = db.Create(&proxySession).Error
	require.NoError(t, err)

	// Load the session (which should update last_accessed)
	session := sessions.NewSession(store, "test_session")
	session.ID = sessionKey
	err = store.load(session)
	assert.NoError(t, err)

	// Verify last_accessed was updated
	var updated ProxySession
	err = db.First(&updated, "session_key = ?", sessionKey).Error
	require.NoError(t, err)
	
	// The last_accessed time should be more recent than the original time
	assert.True(t, updated.LastAccessed.After(originalTime))
}
