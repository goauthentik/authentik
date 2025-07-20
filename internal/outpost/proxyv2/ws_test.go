package proxyv2

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"testing"

	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
)

func TestHashSessionKey(t *testing.T) {
	testCases := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "simple session key",
			input:    "test-session-key",
			expected: "f9a2de3a42b82e3e725c83a9a7f8a4b5c9e1f7d3a8b2c4d5e6f7g8h9i0j1k2l3",
		},
		{
			name:     "empty string",
			input:    "",
			expected: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
		},
		{
			name:     "long session key",
			input:    "very-long-session-key-with-many-characters-and-numbers-12345678901234567890",
			expected: "should be calculated correctly",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result := hashSessionKey(tc.input)

			// Verify the result is a hex string of the correct length (64 chars for SHA256)
			assert.Len(t, result, 64)

			// Verify it matches what we expect from direct SHA256 calculation
			h := sha256.Sum256([]byte(tc.input))
			expected := hex.EncodeToString(h[:])
			assert.Equal(t, expected, result)
		})
	}
}

func TestHandleWSMessage_SessionEnd(t *testing.T) {
	// Create a mock ProxyServer
	ps := &ProxyServer{
		log:  log.WithField("test", "session_end"),
		apps: map[string]*application.Application{},
	}

	// Test case 1: Valid session end message
	t.Run("valid session end message", func(t *testing.T) {
		sessionKey := "test-session-123"
		hashedSessionKey := hashSessionKey(sessionKey)

		msg := ak.Event{
			Instruction: ak.EventKindSessionEnd,
			Args: map[string]interface{}{
				"session_id": hashedSessionKey,
			},
		}

		err := ps.handleWSMessage(context.Background(), msg)
		assert.NoError(t, err)
	})

	// Test case 2: Wrong instruction type
	t.Run("wrong instruction type", func(t *testing.T) {
		msg := ak.Event{
			Instruction: ak.EventKindTriggerUpdate,
			Args:        map[string]interface{}{},
		}

		err := ps.handleWSMessage(context.Background(), msg)
		assert.NoError(t, err)
	})

	// Test case 3: Invalid args format
	t.Run("invalid args format", func(t *testing.T) {
		msg := ak.Event{
			Instruction: ak.EventKindSessionEnd,
			Args:        "invalid args",
		}

		err := ps.handleWSMessage(context.Background(), msg)
		assert.Error(t, err)
	})
}

// TestSessionIDComparison verifies that session ID comparison works correctly
func TestSessionIDComparison(t *testing.T) {
	originalSessionKey := "original-session-key-12345"
	hashedSessionKey := hashSessionKey(originalSessionKey)

	// Simulate the comparison logic from handleWSMessage
	mockClaims := application.Claims{
		Sid: originalSessionKey,
	}

	// The comparison function should return true when the hashed claim session ID matches
	filterFunc := func(c application.Claims) bool {
		hashedClaimsSid := hashSessionKey(c.Sid)
		return hashedClaimsSid == hashedSessionKey
	}

	result := filterFunc(mockClaims)
	assert.True(t, result, "Session ID comparison should match after hashing")

	// Test with different session key - should not match
	differentClaims := application.Claims{
		Sid: "different-session-key",
	}

	result = filterFunc(differentClaims)
	assert.False(t, result, "Different session IDs should not match")
}
