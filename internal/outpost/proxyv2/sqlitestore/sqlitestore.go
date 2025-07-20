package sqlitestore

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/mattn/go-sqlite3"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

// CleanupPolicy defines the cleanup behavior for expired sessions
type CleanupPolicy struct {
	// BatchSize is the maximum number of sessions to delete in a single operation
	BatchSize int
	// SoftDeleteRetentionDays is how long to keep soft-deleted sessions
	SoftDeleteRetentionDays int
	// ExpiredRetentionHours is how long to keep expired sessions before hard deletion
	ExpiredRetentionHours int
	// MaxCleanupDuration is the maximum time a cleanup operation should take
	MaxCleanupDuration time.Duration
	// VacuumThreshold is the number of deletions after which to run VACUUM
	VacuumThreshold int
}

// DefaultCleanupPolicy returns sensible defaults for cleanup operations
func DefaultCleanupPolicy() CleanupPolicy {
	return CleanupPolicy{
		BatchSize:               1000,
		SoftDeleteRetentionDays: 30,
		ExpiredRetentionHours:   24,
		MaxCleanupDuration:      5 * time.Minute,
		VacuumThreshold:         10000,
	}
}

// SQLiteStore stores gorilla sessions in SQLite
type SQLiteStore struct {
	*sessionstore.BaseStore
	// database connection
	db *gorm.DB
	// path to the SQLite database file
	dbPath string
	// mutex to protect database operations
	mu sync.RWMutex
	// closed indicates if the store has been closed
	closed bool
	// cleanup policy
	cleanupPolicy CleanupPolicy
	// cleanup statistics
	lastCleanup   time.Time
	cleanupStats  CleanupStats
	deletionCount int64 // Track deletions for vacuum threshold
}

// CleanupStats tracks cleanup operation statistics
type CleanupStats struct {
	LastRun            time.Time     `json:"last_run"`
	Duration           time.Duration `json:"duration"`
	ExpiredDeleted     int64         `json:"expired_deleted"`
	SoftDeletedCleaned int64         `json:"soft_deleted_cleaned"`
	TotalProcessed     int64         `json:"total_processed"`
	ErrorCount         int64         `json:"error_count"`
	LastVacuum         time.Time     `json:"last_vacuum"`
	VacuumDuration     time.Duration `json:"vacuum_duration"`
}

// GetDB returns the gorm DB
func (s *SQLiteStore) GetDB() *gorm.DB {
	return s.db
}

// NowValue returns the function to get the current time in the database
func (s *SQLiteStore) NowValue() string {
	return "datetime('now')"
}

// GetCleanupStats returns the current cleanup statistics
func (s *SQLiteStore) GetCleanupStats() CleanupStats {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.cleanupStats
}

// GetHealthStatus returns basic health information
func (s *SQLiteStore) GetHealthStatus() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	status := map[string]interface{}{
		"closed":         s.closed,
		"db_path":        s.dbPath,
		"last_cleanup":   s.lastCleanup,
		"cleanup_stats":  s.cleanupStats,
		"deletion_count": s.deletionCount,
	}

	// Test database connectivity
	if sqlDB, err := s.db.DB(); err == nil {
		if pingErr := sqlDB.Ping(); pingErr == nil {
			status["database_connected"] = true
		} else {
			status["database_connected"] = false
			status["ping_error"] = pingErr.Error()
		}
	} else {
		status["database_connected"] = false
		status["db_error"] = err.Error()
	}

	return status
}

// NewSQLiteStore creates a new SQLite-based session store with enhanced features
func NewSQLiteStore(dbPath string, providerID string, sessionOptions *sessions.Options) (*SQLiteStore, error) {
	logger := log.WithFields(log.Fields{
		"component":   "SQLiteStore",
		"method":      "NewSQLiteStore",
		"db_path":     dbPath,
		"provider_id": providerID,
	})

	logger.Debug("Creating new SQLite store")

	// Ensure directory exists
	dir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		logger.WithError(err).Error("Failed to create directory for SQLite database")
		return nil, err
	}

	// Open SQLite database with GORM
	db, err := gorm.Open(sqlite.Open(dbPath+"?_journal=WAL&_timeout=5000"), sessionstore.GormConfig(logger))
	if err != nil {
		logger.WithError(err).Error("Failed to open SQLite database")
		return nil, err
	}

	// Configure connection
	if err := sessionstore.ConfigureConnection(db); err != nil {
		logger.WithError(err).Error("Failed to configure database connection")
		sqlDB, _ := db.DB()
		if sqlDB != nil {
			sqlDB.Close()
		}
		return nil, fmt.Errorf("failed to configure database connection: %w", err)
	}

	// Test connection
	sqlDB, err := db.DB()
	if err != nil {
		logger.WithError(err).Error("Failed to get SQL DB from GORM")
		return nil, err
	}

	if err := sqlDB.Ping(); err != nil {
		logger.WithError(err).Error("Failed to ping SQLite database")
		sqlDB.Close()
		return nil, err
	}

	// Auto-migrate the schema
	if err := sessionstore.MigrateSchema(db, ""); err != nil {
		logger.WithError(err).Error("Failed to auto-migrate schema")
		sqlDB.Close()
		return nil, fmt.Errorf("failed to auto-migrate schema: %w", err)
	}

	// Create the store
	store := &SQLiteStore{
		BaseStore:     sessionstore.NewBaseStore(providerID, "sqlite"),
		db:            db,
		dbPath:        dbPath,
		cleanupPolicy: DefaultCleanupPolicy(),
		cleanupStats:  CleanupStats{},
	}

	// Configure session options if provided
	if sessionOptions != nil {
		store.BaseStore.Options(*sessionOptions)
	}

	// Set key prefix for SQLite sessions
	store.BaseStore.KeyPrefix("authentik_proxy_")

	logger.Debug("SQLite store created successfully")
	return store, nil
}

// SetCleanupPolicy updates the cleanup policy
func (s *SQLiteStore) SetCleanupPolicy(policy CleanupPolicy) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.cleanupPolicy = policy
}

// periodicCleanup runs cleanup at regular intervals
func (s *SQLiteStore) periodicCleanup() {
	logger := log.WithFields(log.Fields{
		"component": "SQLiteStore",
		"method":    "periodicCleanup",
	})

	ticker := time.NewTicker(10 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		if s.closed {
			logger.Debug("Store is closed, stopping periodic cleanup")
			return
		}

		if err := s.cleanupWithPolicy(); err != nil {
			logger.WithError(err).Warning("Failed to clean up expired sessions")
		}
	}
}

// cleanupWithPolicy performs cleanup using the configured policy
func (s *SQLiteStore) cleanupWithPolicy() error {
	ctx, cancel := context.WithTimeout(context.Background(), s.cleanupPolicy.MaxCleanupDuration)
	defer cancel()

	return s.CleanupExpiredWithPolicy(ctx, s.cleanupPolicy)
}

// CleanupExpiredWithPolicy removes expired sessions using the specified policy
func (s *SQLiteStore) CleanupExpiredWithPolicy(ctx context.Context, policy CleanupPolicy) error {
	logger := log.WithFields(log.Fields{
		"component":    "SQLiteStore",
		"method":       "CleanupExpiredWithPolicy",
		"batch_size":   policy.BatchSize,
		"max_duration": policy.MaxCleanupDuration,
	})

	start := time.Now()

	s.mu.Lock()
	defer s.mu.Unlock()

	stats := CleanupStats{
		LastRun: start,
	}

	now := time.Now()
	expiredCutoff := now.Add(-time.Duration(policy.ExpiredRetentionHours) * time.Hour)
	softDeleteCutoff := now.AddDate(0, 0, -policy.SoftDeleteRetentionDays)

	// Clean up expired sessions in batches
	expiredDeleted, err := s.cleanupExpiredBatch(ctx, expiredCutoff, policy.BatchSize)
	if err != nil {
		stats.ErrorCount++
		logger.WithError(err).Warning("Failed to cleanup expired sessions")
	} else {
		stats.ExpiredDeleted = expiredDeleted
		s.deletionCount += expiredDeleted
	}

	// Clean up old soft-deleted sessions in batches
	softDeletedCleaned, err := s.cleanupSoftDeletedBatch(ctx, softDeleteCutoff, policy.BatchSize)
	if err != nil {
		stats.ErrorCount++
		logger.WithError(err).Warning("Failed to cleanup soft-deleted sessions")
	} else {
		stats.SoftDeletedCleaned = softDeletedCleaned
		s.deletionCount += softDeletedCleaned
	}

	stats.TotalProcessed = stats.ExpiredDeleted + stats.SoftDeletedCleaned
	stats.Duration = time.Since(start)
	s.cleanupStats = stats
	s.lastCleanup = start

	logger.WithFields(log.Fields{
		"expired_deleted":      stats.ExpiredDeleted,
		"soft_deleted_cleaned": stats.SoftDeletedCleaned,
		"total_processed":      stats.TotalProcessed,
		"duration":             stats.Duration,
		"error_count":          stats.ErrorCount,
	}).Info("Cleanup completed")

	// Run VACUUM if threshold is reached
	if s.deletionCount >= int64(policy.VacuumThreshold) {
		if err := s.vacuum(ctx); err != nil {
			logger.WithError(err).Warning("Failed to vacuum database")
		} else {
			s.deletionCount = 0 // Reset counter after successful vacuum
		}
	}

	return nil
}

// cleanupExpiredBatch removes expired sessions in batches
func (s *SQLiteStore) cleanupExpiredBatch(ctx context.Context, cutoff time.Time, batchSize int) (int64, error) {
	var totalDeleted int64

	for {
		select {
		case <-ctx.Done():
			return totalDeleted, ctx.Err()
		default:
		}

		// Delete a batch of expired sessions
		result := s.db.WithContext(ctx).
			Where("expires < ? AND expires IS NOT NULL", cutoff).
			Limit(batchSize).
			Delete(&sessionstore.ProxySession{})

		if result.Error != nil {
			return totalDeleted, result.Error
		}

		deleted := result.RowsAffected
		totalDeleted += deleted

		// If we deleted fewer than the batch size, we're done
		if deleted < int64(batchSize) {
			break
		}

		// Small delay between batches to avoid overwhelming the database
		time.Sleep(10 * time.Millisecond)
	}

	return totalDeleted, nil
}

// cleanupSoftDeletedBatch removes old soft-deleted sessions in batches
func (s *SQLiteStore) cleanupSoftDeletedBatch(ctx context.Context, cutoff time.Time, batchSize int) (int64, error) {
	var totalDeleted int64

	for {
		select {
		case <-ctx.Done():
			return totalDeleted, ctx.Err()
		default:
		}

		// Hard delete old soft-deleted sessions
		result := s.db.WithContext(ctx).Unscoped().
			Where("deleted_at IS NOT NULL AND deleted_at < ?", cutoff).
			Limit(batchSize).
			Delete(&sessionstore.ProxySession{})

		if result.Error != nil {
			return totalDeleted, result.Error
		}

		deleted := result.RowsAffected
		totalDeleted += deleted

		// If we deleted fewer than the batch size, we're done
		if deleted < int64(batchSize) {
			break
		}

		// Small delay between batches
		time.Sleep(10 * time.Millisecond)
	}

	return totalDeleted, nil
}

// vacuum runs VACUUM on the SQLite database to reclaim space
func (s *SQLiteStore) vacuum(ctx context.Context) error {
	logger := log.WithField("component", "SQLiteStore").WithField("method", "vacuum")

	start := time.Now()
	logger.Info("Starting database vacuum")

	result := s.db.WithContext(ctx).Exec("VACUUM")
	if result.Error != nil {
		return result.Error
	}

	duration := time.Since(start)

	logger.WithField("duration", duration).Info("Database vacuum completed")
	return nil
}

// CleanupExpired removes expired sessions and old soft-deleted sessions, returning count of deleted sessions
func (s *SQLiteStore) CleanupExpired(ctx context.Context) (int64, error) {
	policy := s.cleanupPolicy
	err := s.CleanupExpiredWithPolicy(ctx, policy)
	if err != nil {
		return 0, err
	}

	s.mu.RLock()
	stats := s.cleanupStats
	s.mu.RUnlock()

	return stats.TotalProcessed, nil
}

// Close closes the SQLite store with proper cleanup
func (s *SQLiteStore) Close() error {
	logger := log.WithFields(log.Fields{
		"component": "SQLiteStore",
		"method":    "Close",
	})

	s.mu.Lock()
	defer s.mu.Unlock()

	if s.closed {
		return nil
	}

	logger.Debug("Closing SQLite store")

	// Perform final cleanup
	if err := s.cleanupWithPolicy(); err != nil {
		logger.WithError(err).Warning("Failed to perform final cleanup")
	}

	// Close database connection
	sqlDB, err := s.db.DB()
	if err != nil {
		logger.WithError(err).Error("Failed to get SQL DB from GORM")
		s.closed = true
		return err
	}

	err = sqlDB.Close()
	if err == nil {
		s.closed = true
		logger.Info("SQLite store closed successfully")
	}
	return err
}

// Get returns a session for the given name after adding it to the registry
func (s *SQLiteStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry
func (s *SQLiteStore) New(r *http.Request, name string) (*sessions.Session, error) {
	session, err := s.CreateNewSession(s, r, name)
	if err != nil {
		return session, err
	}

	if session.ID == "" {
		return session, nil
	}

	// Load session data from store
	err = s.Load(r.Context(), s, session)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return session, nil
		}
		return session, err
	}

	session.IsNew = false
	return session, nil
}

// Save adds a single session to the response
func (s *SQLiteStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	if session.Options.MaxAge <= 0 {
		if err := s.BaseStore.Delete(r.Context(), s, session); err != nil {
			return err
		}
		return s.HandleSessionSave(w, session)
	}

	if err := s.HandleSessionSave(w, session); err != nil {
		return err
	}

	// Save to database
	return s.BaseStore.Save(r.Context(), s, session)
}

// Delete deletes a session from SQLite (public version)
func (s *SQLiteStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.BaseStore.Delete(ctx, s, session)
}

// GetAllSessions returns all sessions in the database
func (s *SQLiteStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	return s.BaseStore.GetAllSessions(ctx, s)
}

// StartPeriodicCleanup starts the periodic cleanup of expired sessions
func (s *SQLiteStore) StartPeriodicCleanup(ctx context.Context, intervalSeconds int) {
	logger := log.WithFields(log.Fields{
		"component": "SQLiteStore",
		"method":    "StartPeriodicCleanup",
		"interval":  intervalSeconds,
	})
	logger.Debug("Starting periodic cleanup")

	go func() {
		ticker := time.NewTicker(time.Duration(intervalSeconds) * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				logger.Debug("Context cancelled, stopping periodic cleanup")
				return
			case <-ticker.C:
				if err := s.cleanupWithPolicy(); err != nil {
					logger.WithError(err).Warning("Failed to clean up expired sessions")
				}
			}
		}
	}()
}
