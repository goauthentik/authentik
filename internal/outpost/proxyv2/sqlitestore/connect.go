package sqlitestore

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

// SQLiteConnectionConfig holds connection configuration for SQLite
type SQLiteConnectionConfig struct {
	BasePath        string
	DatabaseName    string
	CleanupInterval int
}

// LoadSQLiteConfig loads SQLite configuration from the global config
func LoadSQLiteConfig() SQLiteConnectionConfig {
	return SQLiteConnectionConfig{
		DatabaseName:    "sessions.sqlite",
		CleanupInterval: config.Get().SQLite.CleanupInterval,
	}
}

// DetermineBasePath determines the best base path for SQLite database
func (c SQLiteConnectionConfig) DetermineBasePath(logger *log.Entry) (string, error) {
	var basePath string

	// Try /dev/shm first (shared memory, faster)
	if _, err := os.Stat("/dev/shm"); err == nil {
		basePath = "/dev/shm/authentik-sessions"
		logger.WithField("path", basePath).Debug("Using /dev/shm for SQLite database")
	} else {
		// Fall back to temp directory
		basePath = filepath.Join(os.TempDir(), "authentik-sessions")
		logger.WithField("path", basePath).Debug("Using temp directory for SQLite database")
	}

	// Create the directory if it doesn't exist
	if err := os.MkdirAll(basePath, 0755); err != nil {
		logger.WithError(err).WithField("path", basePath).Error("Failed to create directory for SQLite database")
		return "", fmt.Errorf("failed to create directory for SQLite database: %w", err)
	}

	return basePath, nil
}

// BuildDatabasePath builds the full path to the SQLite database file
func (c SQLiteConnectionConfig) BuildDatabasePath(logger *log.Entry) (string, error) {
	basePath, err := c.DetermineBasePath(logger)
	if err != nil {
		return "", err
	}

	dbPath := filepath.Join(basePath, c.DatabaseName)

	logger.WithFields(log.Fields{
		"base_path": basePath,
		"db_path":   dbPath,
	}).Debug("Built SQLite database path")

	return dbPath, nil
}

// ValidateConfig validates the SQLite configuration for standalone outposts
func (c SQLiteConnectionConfig) ValidateConfig(logger *log.Entry) error {
	logger.WithFields(log.Fields{
		"database_name":    c.DatabaseName,
		"cleanup_interval": c.CleanupInterval,
	}).Debug("Loaded SQLite configuration for standalone outpost")

	// Check if we can create the database path
	dbPath, err := c.BuildDatabasePath(logger)
	if err != nil {
		return fmt.Errorf("failed to determine SQLite database path: %w", err)
	}

	// Check if the directory is writable
	testFile := filepath.Join(filepath.Dir(dbPath), ".test_write")
	if file, err := os.Create(testFile); err != nil {
		logger.WithError(err).WithField("path", dbPath).Error("SQLite database directory is not writable")
		return fmt.Errorf("SQLite database directory is not writable: %w", err)
	} else {
		file.Close()
		os.Remove(testFile)
	}

	return nil
}

// CreateStoreFromConfig creates a new SQLite store with validation
func CreateStoreFromConfig(providerID string, sessionOptions *sessions.Options, logger *log.Entry) (*SQLiteStore, error) {
	config := LoadSQLiteConfig()

	if err := config.ValidateConfig(logger); err != nil {
		return nil, err
	}

	dbPath, err := config.BuildDatabasePath(logger)
	if err != nil {
		return nil, fmt.Errorf("failed to build database path: %w", err)
	}

	logger.WithFields(log.Fields{
		"db_path":     dbPath,
		"provider_id": providerID,
	}).Info("Using shared SQLite database for session storage")

	store, err := NewSQLiteStore(dbPath, providerID, sessionOptions)
	if err != nil {
		logger.WithError(err).WithField("db_path", dbPath).Error("Failed to create SQLite store")
		return nil, fmt.Errorf("failed to create SQLite store: %w", err)
	}

	// Start periodic cleanup of expired sessions
	logger.WithField("interval_seconds", config.CleanupInterval).Debug("Starting periodic cleanup of expired sessions")
	store.StartPeriodicCleanup(context.Background(), config.CleanupInterval)

	logger.WithField("path", dbPath).Info("Using SQLite session backend")
	return store, nil
}
