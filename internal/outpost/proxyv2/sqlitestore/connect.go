package sqlitestore

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

// SQLiteConnectionConfig holds connection configuration for SQLite
type SQLiteConnectionConfig struct {
	BasePath        string
	DatabaseName    string
	CleanupInterval int
	// Performance settings
	WALMode         bool
	JournalMode     string
	CacheSize       int
	TempStore       string
	SynchronousMode string
	BusyTimeout     int
	// Security settings
	SecureDelete bool
	ForeignKeys  bool
}

// LoadSQLiteConfig loads SQLite configuration from the global config with smart defaults
func LoadSQLiteConfig() SQLiteConnectionConfig {
	cfg := config.Get()

	walMode := true
	journalMode := "WAL"
	cacheSize := -8000 // 8MB cache
	tempStore := "memory"
	synchronousMode := "NORMAL"
	busyTimeout := 5000

	return SQLiteConnectionConfig{
		DatabaseName:    "sessions.sqlite",
		CleanupInterval: getCleanupInterval(cfg),
		WALMode:         walMode,
		JournalMode:     journalMode,
		CacheSize:       cacheSize,
		TempStore:       tempStore,
		SynchronousMode: synchronousMode,
		BusyTimeout:     busyTimeout,
		SecureDelete:    true,
		ForeignKeys:     true,
	}
}

// getCleanupInterval determines appropriate cleanup interval
func getCleanupInterval(cfg *config.Config) int {
	if cfg.SQLite.CleanupInterval > 0 {
		return cfg.SQLite.CleanupInterval
	}
	return 3600
}

// DetermineBasePath determines the best base path for SQLite database with enhanced logic
func (c SQLiteConnectionConfig) DetermineBasePath(logger *log.Entry) (string, error) {
	var basePath string
	var pathType string

	// Priority order for database location:
	// 1. Explicit user configuration
	// 2. /dev/shm (if available and has sufficient space)
	// 3. /tmp/authentik-sessions
	// 4. OS temp directory fallback

	if c.BasePath != "" {
		basePath = c.BasePath
		pathType = "user-configured"
	} else if canUseShm(logger) {
		basePath = "/dev/shm/authentik-sessions"
		pathType = "shared-memory"
	} else {
		basePath = filepath.Join(os.TempDir(), "authentik-sessions")
		pathType = "temp-directory"
	}

	logger.WithFields(log.Fields{
		"path":      basePath,
		"path_type": pathType,
		"os":        runtime.GOOS,
	}).Info("Selected SQLite database location")

	// Create the directory
	if err := os.MkdirAll(basePath, 0750); err != nil {
		logger.WithError(err).WithField("path", basePath).Error("Failed to create directory for SQLite database")
		return "", fmt.Errorf("failed to create directory for SQLite database: %w", err)
	}

	// Verify we can write to the directory
	testFile := filepath.Join(basePath, ".write_test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		logger.WithError(err).WithField("path", basePath).Error("Directory is not writable")
		return "", fmt.Errorf("directory %s is not writable: %w", basePath, err)
	}
	os.Remove(testFile) // Clean up test file

	return basePath, nil
}

// canUseShm checks if /dev/shm is available and has sufficient space
func canUseShm(logger *log.Entry) bool {
	shmPath := "/dev/shm"

	// Check if /dev/shm exists and is writable
	if stat, err := os.Stat(shmPath); err != nil || !stat.IsDir() {
		logger.Debug("/dev/shm not available")
		return false
	}

	// Test write permissions
	testFile := filepath.Join(shmPath, ".authentik_test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		logger.WithError(err).Debug("/dev/shm not writable")
		return false
	}
	os.Remove(testFile)

	logger.Debug("Using /dev/shm for SQLite database")
	return true
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
		"db_name":   c.DatabaseName,
	}).Debug("Built SQLite database path")

	return dbPath, nil
}

// BuildConnectionString builds the SQLite connection string with all options
func (c SQLiteConnectionConfig) BuildConnectionString(dbPath string) string {
	params := make(map[string]string)

	// Journal mode
	if c.WALMode {
		params["_journal"] = "WAL"
	} else {
		params["_journal"] = c.JournalMode
	}

	// Performance parameters
	params["_timeout"] = strconv.Itoa(c.BusyTimeout)
	params["cache"] = "shared"
	params["_cache_size"] = strconv.Itoa(c.CacheSize)
	params["_temp_store"] = c.TempStore
	params["_synchronous"] = c.SynchronousMode

	// Security parameters
	if c.SecureDelete {
		params["_secure_delete"] = "on"
	}
	if c.ForeignKeys {
		params["_foreign_keys"] = "on"
	}

	// Build connection string
	connStr := dbPath + "?"
	first := true
	for key, value := range params {
		if !first {
			connStr += "&"
		}
		connStr += key + "=" + value
		first = false
	}

	return connStr
}

// ValidateConfig validates the SQLite configuration with comprehensive checks
func (c SQLiteConnectionConfig) ValidateConfig(logger *log.Entry) error {
	var errors []string

	// Validate cleanup interval
	if c.CleanupInterval <= 0 {
		logger.Warning("SQLite cleanup interval is not set or invalid, using default")
		c.CleanupInterval = 3600
	} else if c.CleanupInterval < 60 {
		errors = append(errors, "cleanup interval too low (minimum 60 seconds)")
	}

	// Validate cache size
	if c.CacheSize > 0 || c.CacheSize < -64000 {
		errors = append(errors, "cache size should be negative (KB) and reasonable (-1000 to -64000)")
	}

	// Validate busy timeout
	if c.BusyTimeout < 1000 || c.BusyTimeout > 30000 {
		errors = append(errors, "busy timeout should be between 1000ms and 30000ms")
	}

	// Validate journal mode
	validJournalModes := []string{"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"}
	validMode := false
	for _, mode := range validJournalModes {
		if c.JournalMode == mode {
			validMode = true
			break
		}
	}
	if !validMode {
		errors = append(errors, fmt.Sprintf("invalid journal mode %s", c.JournalMode))
	}

	// Validate synchronous mode
	validSyncModes := []string{"OFF", "NORMAL", "FULL", "EXTRA"}
	validSync := false
	for _, mode := range validSyncModes {
		if c.SynchronousMode == mode {
			validSync = true
			break
		}
	}
	if !validSync {
		errors = append(errors, fmt.Sprintf("invalid synchronous mode %s", c.SynchronousMode))
	}

	if len(errors) > 0 {
		return fmt.Errorf("SQLite configuration validation failed: %v", errors)
	}

	logger.WithFields(log.Fields{
		"cleanup_interval": c.CleanupInterval,
		"wal_mode":         c.WALMode,
		"cache_size":       c.CacheSize,
		"busy_timeout":     c.BusyTimeout,
		"synchronous_mode": c.SynchronousMode,
		"secure_delete":    c.SecureDelete,
		"foreign_keys":     c.ForeignKeys,
	}).Debug("SQLite configuration validated")

	return nil
}

// CreateStoreFromConfig creates a new SQLite store with comprehensive validation and optimization
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
		"wal_mode":    config.WALMode,
		"cache_size":  config.CacheSize,
	}).Info("Initializing SQLite session store")

	// Build optimized connection string
	connStr := config.BuildConnectionString(dbPath)

	// Open database with GORM and optimized settings
	db, err := gorm.Open(sqlite.Open(connStr), sessionstore.GormConfig(logger))
	if err != nil {
		return nil, fmt.Errorf("failed to open SQLite database: %w", err)
	}

	// Configure connection pool with SQLite-specific settings
	if err := sessionstore.ConfigureConnection(db); err != nil {
		logger.WithError(err).Error("Failed to configure database connection")
		if sqlDB, _ := db.DB(); sqlDB != nil {
			sqlDB.Close()
		}
		return nil, fmt.Errorf("failed to configure database connection: %w", err)
	}

	// Test connection
	if sqlDB, err := db.DB(); err != nil {
		return nil, fmt.Errorf("failed to get SQL DB from GORM: %w", err)
	} else if err := sqlDB.Ping(); err != nil {
		sqlDB.Close()
		return nil, fmt.Errorf("failed to ping SQLite database: %w", err)
	}

	// Auto-migrate the schema
	if err := sessionstore.MigrateSchema(db, ""); err != nil {
		if sqlDB, _ := db.DB(); sqlDB != nil {
			sqlDB.Close()
		}
		return nil, fmt.Errorf("failed to auto-migrate schema: %w", err)
	}

	// Create the store
	store := &SQLiteStore{
		BaseStore: sessionstore.NewBaseStore(providerID, "sqlite"),
		db:        db,
		dbPath:    dbPath,
	}

	// Configure session options if provided
	if sessionOptions != nil {
		store.BaseStore.Options(*sessionOptions)
	}

	// Set key prefix for SQLite sessions
	store.BaseStore.KeyPrefix("authentik_proxy_")

	// Start periodic cleanup of expired sessions
	logger.WithField("interval_seconds", config.CleanupInterval).Debug("Starting periodic cleanup of expired sessions")
	store.StartPeriodicCleanup(context.Background(), config.CleanupInterval)

	logger.WithField("path", dbPath).Info("SQLite session store initialized successfully")
	return store, nil
}
