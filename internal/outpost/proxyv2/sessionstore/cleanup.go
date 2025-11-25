package sessionstore

import (
	"context"
	"sync"
	"time"

	log "github.com/sirupsen/logrus"
)

const SessionCleanupInterval = 5 * time.Minute

// CleanupStore defines the interface for stores that support cleanup
type CleanupStore interface {
	CleanupExpired(ctx context.Context) error
}

// CleanupManager manages periodic cleanup for session stores
type CleanupManager struct {
	store         CleanupStore
	log           *log.Entry
	cancel        context.CancelFunc
	done          chan struct{}
	mu            sync.Mutex
	cleanupCtx    context.Context
	cleanupCancel context.CancelFunc
}

// NewCleanupManager creates a new cleanup manager for the given store
func NewCleanupManager(store CleanupStore, logger *log.Entry) *CleanupManager {
	return &CleanupManager{
		store: store,
		log:   logger,
	}
}

// Start begins the periodic cleanup goroutine
func (cm *CleanupManager) Start() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.cancel != nil {
		return // Already running
	}

	ctx, cancel := context.WithCancel(context.Background())
	cm.cancel = cancel
	cm.done = make(chan struct{})

	go func() {
		defer close(cm.done)
		cm.log.Info("Scheduling session cleanup job")
		ticker := time.NewTicker(SessionCleanupInterval)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				cm.log.Info("Stopping session cleanup job")
				return
			case <-ticker.C:
				cm.runCleanup()
			}
		}
	}()
}

// runCleanup executes a single cleanup operation
func (cm *CleanupManager) runCleanup() {
	cm.mu.Lock()
	if cm.cleanupCtx != nil {
		cm.mu.Unlock()
		cm.log.Warn("Cleanup already in progress, skipping")
		return
	}

	cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 30*time.Second)
	cm.cleanupCtx = cleanupCtx
	cm.cleanupCancel = cleanupCancel
	cm.mu.Unlock()

	defer func() {
		cm.mu.Lock()
		if cm.cleanupCancel != nil {
			cm.cleanupCancel()
		}
		cm.cleanupCtx = nil
		cm.cleanupCancel = nil
		cm.mu.Unlock()
	}()

	cm.log.Debug("Running session cleanup")
	if err := cm.store.CleanupExpired(cleanupCtx); err != nil {
		cm.log.WithError(err).Warn("Session cleanup returned error")
	} else {
		cm.log.Debug("Session cleanup completed successfully")
	}
}

// Stop halts the periodic cleanup goroutine
func (cm *CleanupManager) Stop() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.cancel != nil {
		cm.cancel()
		if cm.done != nil {
			<-cm.done
		}
		cm.cancel = nil
		cm.done = nil
	}
}
