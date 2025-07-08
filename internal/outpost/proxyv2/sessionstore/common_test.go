package sessionstore

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/sessions"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewBaseStore(t *testing.T) {
	providerID := "test-provider-123"
	storeType := "test-store"

	store := NewBaseStore(providerID, storeType)

	assert.NotNil(t, store)
	assert.Equal(t, providerID, store.providerID)
	assert.Equal(t, storeType, store.storeType)
	assert.Equal(t, "session:", store.keyPrefix)
	assert.Equal(t, 86400*30, store.options.MaxAge)
	assert.Equal(t, "/", store.options.Path)
	assert.IsType(t, GobSerializer{}, store.serializer)
	assert.NotNil(t, store.keyGen)
}

func TestBaseStore_Options(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	newOptions := sessions.Options{
		Path:     "/custom",
		MaxAge:   7200,
		HttpOnly: true,
		Secure:   true,
		Domain:   "example.com",
		SameSite: http.SameSiteStrictMode,
	}

	store.Options(newOptions)

	assert.Equal(t, "/custom", store.options.Path)
	assert.Equal(t, 7200, store.options.MaxAge)
	assert.True(t, store.options.HttpOnly)
	assert.True(t, store.options.Secure)
	assert.Equal(t, "example.com", store.options.Domain)
	assert.Equal(t, http.SameSiteStrictMode, store.options.SameSite)
}

func TestBaseStore_KeyPrefix(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	store.KeyPrefix("custom_prefix_")

	assert.Equal(t, "custom_prefix_", store.keyPrefix)
}

func TestBaseStore_KeyGen(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	customKeyGen := func() (string, error) {
		return "custom-key-123", nil
	}

	store.KeyGen(customKeyGen)

	key, err := store.keyGen()
	assert.NoError(t, err)
	assert.Equal(t, "custom-key-123", key)
}

func TestBaseStore_Serializer(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	customSerializer := &testSerializer{}
	store.Serializer(customSerializer)

	assert.Equal(t, customSerializer, store.serializer)
}

func TestBaseStore_GetSessionKey(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")
	store.KeyPrefix("test_prefix_")

	sessionKey := store.GetSessionKey("session123")

	assert.Equal(t, "test_prefix_session123", sessionKey)
}

func TestBaseStore_ProviderID(t *testing.T) {
	providerID := "test-provider-456"
	store := NewBaseStore(providerID, "test-store")

	assert.Equal(t, providerID, store.ProviderID())
}

func TestBaseStore_GetSerializer(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	serializer := store.GetSerializer()

	assert.IsType(t, GobSerializer{}, serializer)
}

func TestBaseStore_GetKeyPrefix(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")
	store.KeyPrefix("test_prefix_")

	assert.Equal(t, "test_prefix_", store.GetKeyPrefix())
}

func TestBaseStore_CalculateExpiry(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	t.Run("Positive MaxAge", func(t *testing.T) {
		session := &sessions.Session{
			Options: &sessions.Options{
				MaxAge: 3600, // 1 hour
			},
		}

		before := time.Now()
		expiry := store.CalculateExpiry(session)
		after := time.Now().Add(3600 * time.Second)

		assert.True(t, expiry.After(before))
		assert.True(t, expiry.Before(after))
	})

	t.Run("Zero MaxAge", func(t *testing.T) {
		session := &sessions.Session{
			Options: &sessions.Options{
				MaxAge: 0,
			},
		}

		before := time.Now()
		expiry := store.CalculateExpiry(session)
		after := time.Now().Add(time.Second)

		assert.True(t, expiry.After(before.Add(-time.Second)))
		assert.True(t, expiry.Before(after))
	})

	t.Run("Negative MaxAge", func(t *testing.T) {
		session := &sessions.Session{
			Options: &sessions.Options{
				MaxAge: -1,
			},
		}

		before := time.Now()
		expiry := store.CalculateExpiry(session)
		after := time.Now().Add(time.Second)

		assert.True(t, expiry.After(before.Add(-time.Second)))
		assert.True(t, expiry.Before(after))
	})
}

func TestBaseStore_TrackOperation(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	// mainly a test to make sure the method doesn't panic, but we don't check the metrics. TODO
	store.TrackOperation("test_operation", 100*time.Millisecond)
}

func TestBaseStore_HandleSessionSave(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	t.Run("MaxAge <= 0", func(t *testing.T) {
		w := httptest.NewRecorder()
		session := sessions.NewSession(&mockSessionStore{}, "test-session")
		session.Options = &sessions.Options{
			MaxAge: -1,
		}

		err := store.HandleSessionSave(w, session)
		assert.NoError(t, err)

		// Check that cookie was set to expire
		cookies := w.Result().Cookies()
		assert.Len(t, cookies, 1)
		assert.Equal(t, "test-session", cookies[0].Name)
		assert.Equal(t, "", cookies[0].Value)
	})

	t.Run("Generate new session ID", func(t *testing.T) {
		w := httptest.NewRecorder()
		session := sessions.NewSession(&mockSessionStore{}, "test-session")
		session.Options = &sessions.Options{
			MaxAge: 3600,
		}

		err := store.HandleSessionSave(w, session)
		assert.NoError(t, err)
		assert.NotEmpty(t, session.ID)

		// Check that cookie was set with session ID
		cookies := w.Result().Cookies()
		assert.Len(t, cookies, 1)
		assert.Equal(t, "test-session", cookies[0].Name)
		assert.Equal(t, session.ID, cookies[0].Value)
	})

	t.Run("Existing session ID", func(t *testing.T) {
		w := httptest.NewRecorder()
		session := sessions.NewSession(&mockSessionStore{}, "test-session")
		session.Options = &sessions.Options{
			MaxAge: 3600,
		}
		session.ID = "existing-session-123"

		err := store.HandleSessionSave(w, session)
		assert.NoError(t, err)
		assert.Equal(t, "existing-session-123", session.ID)

		// Check that cookie was set with existing session ID
		cookies := w.Result().Cookies()
		assert.Len(t, cookies, 1)
		assert.Equal(t, "test-session", cookies[0].Name)
		assert.Equal(t, "existing-session-123", cookies[0].Value)
	})

	t.Run("Key generation error", func(t *testing.T) {
		store.KeyGen(func() (string, error) {
			return "", assert.AnError
		})

		w := httptest.NewRecorder()
		session := sessions.NewSession(&mockSessionStore{}, "test-session")
		session.Options = &sessions.Options{
			MaxAge: 3600,
		}

		err := store.HandleSessionSave(w, session)
		assert.Error(t, err)
		assert.Equal(t, assert.AnError, err)
	})
}

func TestBaseStore_CreateNewSession(t *testing.T) {
	store := NewBaseStore("test-provider", "test-store")

	t.Run("No cookie", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/test", nil)
		mockStore := &mockSessionStore{}

		session, err := store.CreateNewSession(mockStore, req, "test-session")
		assert.NoError(t, err)
		assert.NotNil(t, session)
		assert.Equal(t, "test-session", session.Name())
		assert.True(t, session.IsNew)
		assert.Empty(t, session.ID)
		assert.Equal(t, mockStore, session.Store())
	})

	t.Run("With cookie", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/test", nil)
		req.AddCookie(&http.Cookie{
			Name:  "test-session",
			Value: "cookie-session-123",
		})
		mockStore := &mockSessionStore{}

		session, err := store.CreateNewSession(mockStore, req, "test-session")
		assert.NoError(t, err)
		assert.NotNil(t, session)
		assert.Equal(t, "test-session", session.Name())
		assert.True(t, session.IsNew)
		assert.Equal(t, "cookie-session-123", session.ID)
		assert.Equal(t, mockStore, session.Store())
	})
}

func TestGobSerializer_Serialize(t *testing.T) {
	serializer := GobSerializer{}

	t.Run("Valid session", func(t *testing.T) {
		session := &sessions.Session{
			Values: map[interface{}]interface{}{
				"user":  "testuser",
				"roles": []string{"admin", "user"},
				"age":   25,
			},
		}

		data, err := serializer.Serialize(session)
		assert.NoError(t, err)
		assert.NotEmpty(t, data)
	})

	t.Run("Empty session", func(t *testing.T) {
		session := &sessions.Session{
			Values: map[interface{}]interface{}{},
		}

		data, err := serializer.Serialize(session)
		assert.NoError(t, err)
		assert.NotEmpty(t, data)
	})

	t.Run("Nil values", func(t *testing.T) {
		session := &sessions.Session{
			Values: nil,
		}

		data, err := serializer.Serialize(session)
		assert.NoError(t, err)
		assert.NotEmpty(t, data)
	})
}

func TestGobSerializer_Deserialize(t *testing.T) {
	serializer := GobSerializer{}

	t.Run("Valid data", func(t *testing.T) {
		originalSession := &sessions.Session{
			Values: map[interface{}]interface{}{
				"user":  "testuser",
				"roles": []string{"admin", "user"},
				"age":   25,
			},
		}

		data, err := serializer.Serialize(originalSession)
		require.NoError(t, err)

		newSession := &sessions.Session{}
		err = serializer.Deserialize(data, newSession)
		assert.NoError(t, err)
		assert.Equal(t, "testuser", newSession.Values["user"])
		assert.Equal(t, []string{"admin", "user"}, newSession.Values["roles"])
		assert.Equal(t, 25, newSession.Values["age"])
	})

	t.Run("Empty data", func(t *testing.T) {
		session := &sessions.Session{}
		err := serializer.Deserialize([]byte{}, session)
		assert.Error(t, err)
	})

	t.Run("Invalid data", func(t *testing.T) {
		session := &sessions.Session{}
		err := serializer.Deserialize([]byte("invalid gob data"), session)
		assert.Error(t, err)
	})

	t.Run("Nil data", func(t *testing.T) {
		session := &sessions.Session{}
		err := serializer.Deserialize(nil, session)
		assert.Error(t, err)
	})
}

func TestGobSerializer_RoundTrip(t *testing.T) {
	serializer := GobSerializer{}

	testCases := []map[interface{}]interface{}{
		{
			"string": "value",
			"int":    42,
			"float":  3.14,
			"bool":   true,
			"slice":  []string{"a", "b", "c"},
			"map":    map[string]string{"key": "value"},
		},
		{
			"complex": map[string]interface{}{
				"nested": map[string]int{
					"count": 100,
				},
			},
		},
		{
			"unicode": "测试文本",
		},
	}

	for i, values := range testCases {
		t.Run(fmt.Sprintf("Case %d", i), func(t *testing.T) {
			originalSession := &sessions.Session{Values: values}

			data, err := serializer.Serialize(originalSession)
			require.NoError(t, err)

			newSession := &sessions.Session{}
			err = serializer.Deserialize(data, newSession)
			assert.NoError(t, err)
			assert.Equal(t, values, newSession.Values)
		})
	}
}

func TestGenerateRandomKey(t *testing.T) {
	t.Run("Generate valid key", func(t *testing.T) {
		key, err := GenerateRandomKey()
		assert.NoError(t, err)
		assert.NotEmpty(t, key)
		assert.Greater(t, len(key), 50) // Should be reasonably long
	})

	t.Run("Generate unique keys", func(t *testing.T) {
		keys := make(map[string]bool)
		for i := 0; i < 100; i++ {
			key, err := GenerateRandomKey()
			assert.NoError(t, err)
			assert.False(t, keys[key], "Generated duplicate key: %s", key)
			keys[key] = true
		}
	})

	t.Run("Key format", func(t *testing.T) {
		key, err := GenerateRandomKey()
		assert.NoError(t, err)
		// Should be base32 encoded (no padding)
		assert.NotContains(t, key, "=")
		// Should only contain valid base32 characters
		for _, char := range key {
			assert.True(t,
				(char >= 'A' && char <= 'Z') || (char >= '2' && char <= '7'),
				"Invalid base32 character: %c", char)
		}
	})
}

func TestBaseStore_Integration(t *testing.T) {
	store := NewBaseStore("integration-provider", "integration-store")

	// Configure store
	store.KeyPrefix("integration_")
	store.Options(sessions.Options{
		Path:     "/integration",
		MaxAge:   7200,
		HttpOnly: true,
		Secure:   false,
	})

	// Test session creation
	req := httptest.NewRequest("GET", "/integration/test", nil)
	mockStore := &mockSessionStore{}

	session, err := store.CreateNewSession(mockStore, req, "integration-session")
	assert.NoError(t, err)
	assert.NotNil(t, session)

	// Test session key generation
	sessionKey := store.GetSessionKey("test-id")
	assert.Equal(t, "integration_test-id", sessionKey)

	// Test expiry calculation
	expiry := store.CalculateExpiry(session)
	assert.True(t, expiry.After(time.Now()))
	assert.True(t, expiry.Before(time.Now().Add(7201*time.Second)))
}

func TestBaseStore_ConcurrentOperations(t *testing.T) {
	store := NewBaseStore("concurrent-provider", "concurrent-store")

	// Test concurrent key generation
	keys := make(chan string, 100)
	for i := 0; i < 100; i++ {
		go func() {
			key, err := store.keyGen()
			assert.NoError(t, err)
			keys <- key
		}()
	}

	// Collect all keys
	generatedKeys := make(map[string]bool)
	for i := 0; i < 100; i++ {
		key := <-keys
		assert.False(t, generatedKeys[key], "Generated duplicate key: %s", key)
		generatedKeys[key] = true
	}
}

func TestBaseStore_EdgeCases(t *testing.T) {
	store := NewBaseStore("edge-provider", "edge-store")

	t.Run("Empty provider ID", func(t *testing.T) {
		emptyStore := NewBaseStore("", "test-store")
		assert.Equal(t, "", emptyStore.ProviderID())
	})

	t.Run("Empty store type", func(t *testing.T) {
		emptyStore := NewBaseStore("test-provider", "")
		assert.Equal(t, "", emptyStore.storeType)
	})

	t.Run("Very long session ID", func(t *testing.T) {
		longID := string(make([]byte, 10000))
		for i := range longID {
			longID = longID[:i] + "a" + longID[i+1:]
		}

		sessionKey := store.GetSessionKey(longID)
		assert.Equal(t, "session:"+longID, sessionKey)
	})

	t.Run("Unicode in session ID", func(t *testing.T) {
		unicodeID := "session_测试_🔑"
		sessionKey := store.GetSessionKey(unicodeID)
		assert.Equal(t, "session:"+unicodeID, sessionKey)
	})
}

// Helper types for testing
type testSerializer struct{}

func (ts *testSerializer) Serialize(s *sessions.Session) ([]byte, error) {
	return []byte("test-serialized"), nil
}

func (ts *testSerializer) Deserialize(b []byte, s *sessions.Session) error {
	return nil
}

type mockSessionStore struct{}

func (m *mockSessionStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return nil, nil
}

func (m *mockSessionStore) New(r *http.Request, name string) (*sessions.Session, error) {
	return nil, nil
}

func (m *mockSessionStore) Save(r *http.Request, w http.ResponseWriter, s *sessions.Session) error {
	return nil
}

func (m *mockSessionStore) Options(opts sessions.Options) {}

func (m *mockSessionStore) Close() error { return nil }

func (m *mockSessionStore) Delete(ctx context.Context, session *sessions.Session) error {
	return nil
}

func (m *mockSessionStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	return nil, nil
}

func (m *mockSessionStore) KeyPrefix(keyPrefix string) {}

func (m *mockSessionStore) KeyGen(f KeyGenFunc) {}

func (m *mockSessionStore) Serializer(ss SessionSerializer) {}

// Benchmark tests
func BenchmarkBaseStore_GetSessionKey(b *testing.B) {
	store := NewBaseStore("bench-provider", "bench-store")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.GetSessionKey("benchmark-session-id")
	}
}

func BenchmarkGenerateRandomKey(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		GenerateRandomKey()
	}
}

func BenchmarkGobSerializer_Serialize(b *testing.B) {
	serializer := GobSerializer{}
	session := &sessions.Session{
		Values: map[interface{}]interface{}{
			"user":  "testuser",
			"roles": []string{"admin", "user"},
			"age":   25,
			"data":  bytes.Repeat([]byte("x"), 1000),
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		serializer.Serialize(session)
	}
}

func BenchmarkGobSerializer_Deserialize(b *testing.B) {
	serializer := GobSerializer{}
	session := &sessions.Session{
		Values: map[interface{}]interface{}{
			"user":  "testuser",
			"roles": []string{"admin", "user"},
			"age":   25,
			"data":  bytes.Repeat([]byte("x"), 1000),
		},
	}

	data, _ := serializer.Serialize(session)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		newSession := &sessions.Session{}
		serializer.Deserialize(data, newSession)
	}
}
