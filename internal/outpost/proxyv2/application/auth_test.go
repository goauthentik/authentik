package application

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gorilla/sessions"
	"github.com/mitchellh/mapstructure"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// TestClaimsJSONSerialization tests that Claims can be serialized to JSON and back
func TestClaimsJSONSerialization(t *testing.T) {
	claims := types.Claims{
		Sub:               "user-id-123",
		Exp:               1234567890,
		Email:             "test@example.com",
		Verified:          true,
		Name:              "Test User",
		PreferredUsername: "testuser",
		Groups:            []string{"admin", "user"},
		Entitlements:      []string{"read", "write"},
		Sid:               "session-id-456",
		Proxy: &types.ProxyClaims{
			UserAttributes: map[string]any{
				"custom_field": "custom_value",
				"department":   "engineering",
			},
			BackendOverride: "custom-backend",
			HostHeader:      "example.com",
			IsSuperuser:     true,
		},
		RawToken: "raw.jwt.token",
	}

	// Serialize to JSON
	jsonData, err := json.Marshal(claims)
	require.NoError(t, err)

	// Deserialize back
	var parsedClaims types.Claims
	err = json.Unmarshal(jsonData, &parsedClaims)
	require.NoError(t, err)

	// Verify all fields
	assert.Equal(t, claims.Sub, parsedClaims.Sub)
	assert.Equal(t, claims.Exp, parsedClaims.Exp)
	assert.Equal(t, claims.Email, parsedClaims.Email)
	assert.Equal(t, claims.Verified, parsedClaims.Verified)
	assert.Equal(t, claims.Name, parsedClaims.Name)
	assert.Equal(t, claims.PreferredUsername, parsedClaims.PreferredUsername)
	assert.Equal(t, claims.Groups, parsedClaims.Groups)
	assert.Equal(t, claims.Entitlements, parsedClaims.Entitlements)
	assert.Equal(t, claims.Sid, parsedClaims.Sid)

	// RawToken has no json tag, so it's serialized using the field name
	assert.Equal(t, claims.RawToken, parsedClaims.RawToken)

	// Verify proxy claims
	require.NotNil(t, parsedClaims.Proxy)
	assert.Equal(t, claims.Proxy.BackendOverride, parsedClaims.Proxy.BackendOverride)
	assert.Equal(t, claims.Proxy.HostHeader, parsedClaims.Proxy.HostHeader)
	assert.Equal(t, claims.Proxy.IsSuperuser, parsedClaims.Proxy.IsSuperuser)
	assert.Equal(t, "custom_value", parsedClaims.Proxy.UserAttributes["custom_field"])
	assert.Equal(t, "engineering", parsedClaims.Proxy.UserAttributes["department"])
}

// TestClaimsMapSerialization tests that Claims stored as map[string]any can be converted back
func TestClaimsMapSerialization(t *testing.T) {
	// Simulate how claims are stored in session as map (like from PostgreSQL JSONB)
	claimsMap := map[string]any{
		"sub":                "user-id-123",
		"exp":                float64(1234567890), // json numbers become float64
		"email":              "test@example.com",
		"email_verified":     true,
		"name":               "Test User",
		"preferred_username": "testuser",
		"groups":             []any{"admin", "user"},
		"entitlements":       []any{"read", "write"},
		"sid":                "session-id-456",
		"ak_proxy": map[string]any{
			"user_attributes": map[string]any{
				"custom_field": "custom_value",
			},
			"backend_override": "custom-backend",
			"host_header":      "example.com",
			"is_superuser":     true,
		},
		"raw_token": "not-a-real-token",
	}

	// Convert map to Claims using mapstructure marshaling (like getClaimsFromSession does)
	var claims types.Claims
	err := mapstructure.Decode(claimsMap, &claims)
	require.NoError(t, err)

	// Verify fields
	assert.Equal(t, "user-id-123", claims.Sub)
	assert.Equal(t, 1234567890, claims.Exp)
	assert.Equal(t, "test@example.com", claims.Email)
	assert.True(t, claims.Verified)
	assert.Equal(t, "Test User", claims.Name)
	assert.Equal(t, "testuser", claims.PreferredUsername)
	assert.Equal(t, []string{"admin", "user"}, claims.Groups)
	assert.Equal(t, []string{"read", "write"}, claims.Entitlements)
	assert.Equal(t, "session-id-456", claims.Sid)
	assert.Equal(t, "not-a-real-token", claims.RawToken)

	// Verify proxy claims
	require.NotNil(t, claims.Proxy)
	assert.Equal(t, "custom-backend", claims.Proxy.BackendOverride)
	assert.Equal(t, "example.com", claims.Proxy.HostHeader)
	assert.True(t, claims.Proxy.IsSuperuser)
	assert.Equal(t, "custom_value", claims.Proxy.UserAttributes["custom_field"])
}

// TestClaimsMinimalFields tests that Claims work with minimal required fields
func TestClaimsMinimalFields(t *testing.T) {
	claimsMap := map[string]any{
		"sub": "user-id-123",
		"exp": float64(1234567890),
	}

	jsonData, err := json.Marshal(claimsMap)
	require.NoError(t, err)

	var claims types.Claims
	err = json.Unmarshal(jsonData, &claims)
	require.NoError(t, err)

	assert.Equal(t, "user-id-123", claims.Sub)
	assert.Equal(t, 1234567890, claims.Exp)
	assert.Empty(t, claims.Email)
	assert.Empty(t, claims.Name)
	assert.Empty(t, claims.Groups)
	assert.Nil(t, claims.Proxy)
}

// TestClaimsWithEmptyArrays tests that empty arrays are handled correctly
func TestClaimsWithEmptyArrays(t *testing.T) {
	claimsMap := map[string]any{
		"sub":          "user-id-123",
		"exp":          float64(1234567890),
		"groups":       []any{},
		"entitlements": []any{},
	}

	jsonData, err := json.Marshal(claimsMap)
	require.NoError(t, err)

	var claims types.Claims
	err = json.Unmarshal(jsonData, &claims)
	require.NoError(t, err)

	assert.Equal(t, "user-id-123", claims.Sub)
	assert.NotNil(t, claims.Groups)
	assert.NotNil(t, claims.Entitlements)
	assert.Len(t, claims.Groups, 0)
	assert.Len(t, claims.Entitlements, 0)
}

// TestClaimsWithNullProxyClaims tests that null proxy claims don't cause issues
func TestClaimsWithNullProxyClaims(t *testing.T) {
	claimsMap := map[string]any{
		"sub":      "user-id-123",
		"exp":      float64(1234567890),
		"ak_proxy": nil,
	}

	jsonData, err := json.Marshal(claimsMap)
	require.NoError(t, err)

	var claims types.Claims
	err = json.Unmarshal(jsonData, &claims)
	require.NoError(t, err)

	assert.Equal(t, "user-id-123", claims.Sub)
	assert.Nil(t, claims.Proxy)
}

// TestGetClaimsFromSession_Success tests successful retrieval of claims from session
// uses a mock session that returns claims as map[string]any to simulate
// how PostgreSQL storage deserializes JSONB data
func TestGetClaimsFromSession_Success(t *testing.T) {
	// Create a custom mock store that returns claims as map
	store := &mockMapSessionStore{
		claimsMap: map[string]any{
			"sub":                "user-id-123",
			"exp":                float64(1234567890),
			"email":              "test@example.com",
			"email_verified":     true,
			"preferred_username": "testuser",
			"groups":             []any{"admin", "user"},
		},
	}

	app := &Application{
		sessions: store,
	}

	req := httptest.NewRequest("GET", "/", nil)

	// Test getClaimsFromSession
	claims := app.getClaimsFromSession(nil, req)
	require.NotNil(t, claims)
	assert.Equal(t, "user-id-123", claims.Sub)
	assert.Equal(t, 1234567890, claims.Exp)
	assert.Equal(t, "test@example.com", claims.Email)
	assert.True(t, claims.Verified)
	assert.Equal(t, "testuser", claims.PreferredUsername)
	assert.Equal(t, []string{"admin", "user"}, claims.Groups)
}

// mockMapSessionStore is a mock session store that returns claims as map[string]any
type mockMapSessionStore struct {
	claimsMap map[string]any
}

func (m *mockMapSessionStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	session := sessions.NewSession(m, name)
	if m.claimsMap != nil {
		session.Values[constants.SessionClaims] = m.claimsMap
	}
	return session, nil
}

func (m *mockMapSessionStore) New(r *http.Request, name string) (*sessions.Session, error) {
	return m.Get(r, name)
}

func (m *mockMapSessionStore) Save(r *http.Request, w http.ResponseWriter, s *sessions.Session) error {
	return nil
}

// TestGetClaimsFromSession_NoSession tests behavior when no session exists
func TestGetClaimsFromSession_NoSession(t *testing.T) {
	store := &mockMapSessionStore{
		claimsMap: nil, // No claims
	}

	app := &Application{
		sessions: store,
	}

	req := httptest.NewRequest("GET", "/", nil)

	claims := app.getClaimsFromSession(nil, req)
	assert.Nil(t, claims)
}

// TestGetClaimsFromSession_NoClaims tests behavior when session exists but has no claims
func TestGetClaimsFromSession_NoClaims(t *testing.T) {
	store := &mockMapSessionStore{
		claimsMap: nil, // No claims in session
	}

	app := &Application{
		sessions: store,
	}

	req := httptest.NewRequest("GET", "/", nil)

	claims := app.getClaimsFromSession(nil, req)
	assert.Nil(t, claims)
}

// TestGetClaimsFromSession_InvalidClaimsType tests behavior when claims have wrong type
func TestGetClaimsFromSession_InvalidClaimsType(t *testing.T) {
	store := &mockInvalidClaimsStore{}

	app := &Application{
		sessions: store,
	}

	req := httptest.NewRequest("GET", "/", nil)

	claims := app.getClaimsFromSession(nil, req)
	assert.Nil(t, claims)
}

// mockInvalidClaimsStore returns claims as invalid type (string)
type mockInvalidClaimsStore struct{}

func (m *mockInvalidClaimsStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	session := sessions.NewSession(m, name)
	session.Values[constants.SessionClaims] = "invalid-string-value"
	return session, nil
}

func (m *mockInvalidClaimsStore) New(r *http.Request, name string) (*sessions.Session, error) {
	return m.Get(r, name)
}

func (m *mockInvalidClaimsStore) Save(r *http.Request, w http.ResponseWriter, s *sessions.Session) error {
	return nil
}

// TestClaimsRoundTrip tests full round trip: save Claims, retrieve as map, convert back to Claims
func TestClaimsRoundTrip(t *testing.T) {
	originalClaims := types.Claims{
		Sub:               "user-id-789",
		Exp:               1234567890,
		Email:             "roundtrip@example.com",
		Verified:          true,
		Name:              "Round Trip User",
		PreferredUsername: "roundtripuser",
		Groups:            []string{"group1", "group2", "group3"},
		Entitlements:      []string{"ent1", "ent2"},
		Sid:               "session-789",
		Proxy: &types.ProxyClaims{
			UserAttributes: map[string]any{
				"attr1": "value1",
				"attr2": float64(42),
				"attr3": true,
			},
			BackendOverride: "backend",
			HostHeader:      "host.example.com",
			IsSuperuser:     false,
		},
	}

	// Step 1: Serialize Claims to JSON (simulating storage)
	jsonData, err := json.Marshal(originalClaims)
	require.NoError(t, err)

	// Step 2: Deserialize to map[string]any (simulating PostgreSQL load)
	var claimsMap map[string]any
	err = json.Unmarshal(jsonData, &claimsMap)
	require.NoError(t, err)

	// Step 3: Convert map back to Claims (simulating getClaimsFromSession)
	jsonData2, err := json.Marshal(claimsMap)
	require.NoError(t, err)

	var retrievedClaims types.Claims
	err = json.Unmarshal(jsonData2, &retrievedClaims)
	require.NoError(t, err)

	// Verify all fields match
	assert.Equal(t, originalClaims.Sub, retrievedClaims.Sub)
	assert.Equal(t, originalClaims.Exp, retrievedClaims.Exp)
	assert.Equal(t, originalClaims.Email, retrievedClaims.Email)
	assert.Equal(t, originalClaims.Verified, retrievedClaims.Verified)
	assert.Equal(t, originalClaims.Name, retrievedClaims.Name)
	assert.Equal(t, originalClaims.PreferredUsername, retrievedClaims.PreferredUsername)
	assert.Equal(t, originalClaims.Groups, retrievedClaims.Groups)
	assert.Equal(t, originalClaims.Entitlements, retrievedClaims.Entitlements)
	assert.Equal(t, originalClaims.Sid, retrievedClaims.Sid)

	require.NotNil(t, retrievedClaims.Proxy)
	assert.Equal(t, originalClaims.Proxy.BackendOverride, retrievedClaims.Proxy.BackendOverride)
	assert.Equal(t, originalClaims.Proxy.HostHeader, retrievedClaims.Proxy.HostHeader)
	assert.Equal(t, originalClaims.Proxy.IsSuperuser, retrievedClaims.Proxy.IsSuperuser)
	assert.Equal(t, "value1", retrievedClaims.Proxy.UserAttributes["attr1"])
	assert.Equal(t, float64(42), retrievedClaims.Proxy.UserAttributes["attr2"])
	assert.Equal(t, true, retrievedClaims.Proxy.UserAttributes["attr3"])
}
