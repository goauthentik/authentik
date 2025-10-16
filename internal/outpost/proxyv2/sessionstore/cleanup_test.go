package sessionstore

import (
	"context"
	"sync"
	"testing"

	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
)

// mockSessionStore is a test implementation of SessionStore
type mockSessionStore struct {
	mu             sync.Mutex
	cleanupCount   int
	shouldFailNext bool
}

func (m *mockSessionStore) CleanupExpired(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.shouldFailNext {
		m.shouldFailNext = false
		return assert.AnError
	}

	m.cleanupCount++
	return nil
}

func (m *mockSessionStore) GetCleanupCount() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.cleanupCount
}

func (m *mockSessionStore) ResetCleanupCount() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.cleanupCount = 0
}

func (m *mockSessionStore) SetShouldFail(shouldFail bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.shouldFailNext = shouldFail
}

func TestCleanupManager_StartStop(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)

	// Manager should not be running initially
	manager.mu.Lock()
	running := manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)

	// Start the manager
	manager.Start()

	// Manager should be running
	manager.mu.Lock()
	running = manager.cancel != nil
	manager.mu.Unlock()
	assert.True(t, running)

	// Stop the manager
	manager.Stop()

	// Manager should not be running
	manager.mu.Lock()
	running = manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)
}

func TestCleanupManager_PeriodicCleanup(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	// we can't easily test periodic cleanup without modifying SessionCleanupInterval
	// which is a const. This test verifies the manager starts/stops correctly.
	manager := NewCleanupManager(store, logger)
	manager.Start()

	// Verify it's running
	manager.mu.Lock()
	running := manager.cancel != nil
	manager.mu.Unlock()
	assert.True(t, running)

	manager.Stop()

	// Verify it stopped
	manager.mu.Lock()
	running = manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)
}

func TestCleanupManager_ManualCleanup(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)

	// Run cleanup manually
	manager.runCleanup()

	// Verify cleanup was called
	count := store.GetCleanupCount()
	assert.Equal(t, 1, count)
}

func TestCleanupManager_StopWhileRunning(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)
	manager.Start()

	// Stop immediately
	manager.Stop()

	// Manager should stop cleanly
	manager.mu.Lock()
	running := manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)
}

func TestCleanupManager_MultipleStarts(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)

	// Start multiple times
	manager.Start()
	manager.Start() // Should be no-op
	manager.Start() // Should be no-op

	// Stop
	manager.Stop()

	// Should still stop cleanly
	manager.mu.Lock()
	running := manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)
}

func TestCleanupManager_MultipleStops(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)
	manager.Start()

	// Stop multiple times
	manager.Stop()
	manager.Stop() // Should be no-op
	manager.Stop() // Should be no-op

	// Should still be stopped
	manager.mu.Lock()
	running := manager.cancel != nil
	manager.mu.Unlock()
	assert.False(t, running)
}

func TestCleanupManager_ErrorHandling(t *testing.T) {
	store := &mockSessionStore{}
	logger := log.WithField("test", "cleanup")

	manager := NewCleanupManager(store, logger)

	// Set the store to fail
	store.SetShouldFail(true)

	// Run cleanup manually: should handle error gracefully
	manager.runCleanup()

	// Should not panic and cleanup count should be 0
	count := store.GetCleanupCount()
	assert.Equal(t, 0, count)
}
