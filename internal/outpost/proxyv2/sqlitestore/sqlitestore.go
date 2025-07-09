package sqlitestore

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/mattn/go-sqlite3"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
)

// SQLiteStore stores gorilla sessions in SQLite
type SQLiteStore struct {
	*sessionstore.BaseStore
	// database connection
	db *sql.DB
	// path to the SQLite database file
	dbPath string
	// mutex to protect database operations
	mu sync.RWMutex
	// flag to indicate if the store is closed
	closed bool
}

// NewSQLiteStore creates a new SQLite-based session store
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

	// Open SQLite database
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	if err != nil {
		logger.WithError(err).Error("Failed to open SQLite database")
		return nil, err
	}

	// Set connection parameters
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)

	// Test connection
	if err := db.Ping(); err != nil {
		logger.WithError(err).Error("Failed to ping SQLite database")
		db.Close()
		return nil, err
	}

	// Create the store
	store := &SQLiteStore{
		BaseStore: sessionstore.NewBaseStore(providerID, "sqlite"),
		db:        db,
		dbPath:    dbPath,
		closed:    false,
	}

	// Configure session options if provided
	if sessionOptions != nil {
		store.BaseStore.Options(*sessionOptions)
	}

	// Set key prefix for SQLite sessions
	store.BaseStore.KeyPrefix("authentik_proxy_session_")

	// Create tables and indexes
	if err := store.createTables(); err != nil {
		logger.WithError(err).Error("Failed to create tables")
		db.Close()
		return nil, err
	}

	// Start cleanup goroutine
	go store.periodicCleanup()

	logger.Debug("SQLite store created successfully")
	return store, nil
}

// createTables creates the necessary tables and indexes
func (s *SQLiteStore) createTables() error {
	logger := log.WithField("component", "SQLiteStore").WithField("method", "createTables")

	// Create the sessions table
	_, err := s.db.Exec(`
		CREATE TABLE IF NOT EXISTS authentik_outposts_proxysession (
			uuid TEXT PRIMARY KEY,
			session_key TEXT NOT NULL,
			data BLOB NOT NULL,
			expires TIMESTAMP,
			expiring BOOLEAN NOT NULL DEFAULT 0,
			provider_id TEXT NOT NULL,
			claims TEXT,
			redirect TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			UNIQUE(session_key, provider_id)
		)
	`)
	if err != nil {
		logger.WithError(err).Error("Failed to create sessions table")
		return err
	}

	// Create indexes
	indexes := []string{
		`CREATE INDEX IF NOT EXISTS idx_authentik_outposts_proxysession_key_provider 
		ON authentik_outposts_proxysession(session_key, provider_id)`,
		`CREATE INDEX IF NOT EXISTS idx_authentik_outposts_proxysession_expires 
		ON authentik_outposts_proxysession(expires)`,
	}

	for _, index := range indexes {
		if _, err := s.db.Exec(index); err != nil {
			logger.WithError(err).Error("Failed to create index")
			return err
		}
	}

	return nil
}

// periodicCleanup runs cleanup at regular intervals
func (s *SQLiteStore) periodicCleanup() {
	logger := log.WithFields(log.Fields{
		"component": "SQLiteStore",
		"method":    "periodicCleanup",
	})

	logger.Debug("Starting periodic cleanup")
	ticker := time.NewTicker(15 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		logger.Debug("Running scheduled cleanup")
		if err := s.Cleanup(); err != nil {
			logger.WithError(err).Error("Error during scheduled cleanup")
		}
	}
}

// Cleanup removes expired sessions from the database
func (s *SQLiteStore) Cleanup() error {
	logger := log.WithField("component", "SQLiteStore").WithField("method", "Cleanup")

	s.mu.RLock()
	defer s.mu.RUnlock()

	if s.closed {
		return errors.New("database connection is closed")
	}

	result, err := s.db.Exec(`
		DELETE FROM authentik_outposts_proxysession 
		WHERE expires IS NOT NULL AND expires < datetime('now')
	`)
	if err != nil {
		logger.WithError(err).Error("Error deleting expired sessions")
		return err
	}

	if rowsAffected, err := result.RowsAffected(); err == nil {
		logger.WithField("deleted_sessions", rowsAffected).Info("Deleted expired sessions")
	}

	return nil
}

// Close closes the SQLite store
func (s *SQLiteStore) Close() error {
	logger := log.WithField("component", "SQLiteStore").WithField("db_path", s.dbPath)
	logger.Debug("Closing SQLite store")

	s.mu.Lock()
	defer s.mu.Unlock()

	if s.closed {
		return nil
	}

	// Keep database connection open for session persistence
	logger.Info("Keeping SQLite database connection open for session persistence")
	s.closed = true
	return nil
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
	err = s.load(r.Context(), session)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return session, nil
		}
		return session, err
	}

	session.IsNew = false
	return session, nil
}

// Save adds a single session to the response
func (s *SQLiteStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Handle common save logic (cookie management, ID generation)
	if session.Options.MaxAge <= 0 {
		if err := s.delete(r.Context(), session); err != nil {
			return err
		}
		return s.HandleSessionSave(w, session)
	}

	if err := s.HandleSessionSave(w, session); err != nil {
		return err
	}

	// Save to database
	return s.save(r.Context(), session)
}

// save writes session to SQLite database
func (s *SQLiteStore) save(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("save", time.Since(start))
	}()

	// Serialize session data
	data, err := s.GetSerializer().Serialize(session)
	if err != nil {
		return err
	}

	// Calculate expiry
	expiry := s.CalculateExpiry(session)
	sessionKey := s.GetSessionKey(session.ID)

	// Generate UUID for the session
	uuid, err := sessionstore.GenerateRandomKey()
	if err != nil {
		return err
	}

	// Extract claims and redirect from session
	claims := "{}"
	if c, ok := session.Values["claims"]; ok && c != nil {
		claims = fmt.Sprintf("%v", c)
	}

	redirect := ""
	if r, ok := session.Values["redirect"]; ok && r != nil {
		redirect = fmt.Sprintf("%v", r)
	}

	// Database operation with retry
	return s.executeWithRetry(ctx, func() error {
		_, err := s.db.ExecContext(ctx, `
			INSERT INTO authentik_outposts_proxysession (
				uuid, session_key, data, expires, expiring, provider_id, claims, redirect
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(session_key, provider_id) DO UPDATE SET 
				data = excluded.data, 
				expires = excluded.expires, 
				claims = excluded.claims,
				redirect = excluded.redirect
		`, uuid, sessionKey, data, expiry, true, s.ProviderID(), claims, redirect)
		return err
	})
}

// load reads session from SQLite database
func (s *SQLiteStore) load(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("load", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)
	var data []byte

	err := s.executeWithRetry(ctx, func() error {
		return s.db.QueryRowContext(ctx, `
			SELECT data FROM authentik_outposts_proxysession 
			WHERE session_key = ? AND provider_id = ? AND (expires IS NULL OR expires > datetime('now'))
		`, sessionKey, s.ProviderID()).Scan(&data)
	})

	if err != nil {
		return err
	}

	return s.GetSerializer().Deserialize(data, session)
}

// delete removes session from SQLite database
func (s *SQLiteStore) delete(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("delete", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)

	return s.executeWithRetry(ctx, func() error {
		_, err := s.db.ExecContext(ctx, `
			DELETE FROM authentik_outposts_proxysession 
			WHERE session_key = ? AND provider_id = ?
		`, sessionKey, s.ProviderID())
		return err
	})
}

// executeWithRetry executes a database operation with retry logic
func (s *SQLiteStore) executeWithRetry(_ context.Context, operation func() error) error {
	maxRetries := 3

	for attempt := 0; attempt < maxRetries; attempt++ {
		s.mu.RLock()
		if s.closed {
			s.mu.RUnlock()
			// Try to reconnect if database is closed
			if err := s.reconnect(); err != nil {
				return err
			}
			s.mu.RLock()
		}

		err := operation()
		s.mu.RUnlock()

		if err == nil {
			return nil
		}

		// Handle database closed error
		if strings.Contains(err.Error(), "database is closed") {
			log.WithError(err).Warning("Database is closed, attempting to reconnect")
			if reconnectErr := s.reconnect(); reconnectErr != nil {
				log.WithError(reconnectErr).Error("Failed to reconnect to database")
				return reconnectErr
			}
			continue
		}

		// For other errors, return immediately
		return err
	}

	return errors.New("failed to execute database operation after multiple retries")
}

// reconnect reopens the database connection
func (s *SQLiteStore) reconnect() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	newDb, err := sql.Open("sqlite3", s.dbPath+"?_journal=WAL&_timeout=5000")
	if err != nil {
		return err
	}

	// Set connection parameters
	newDb.SetMaxOpenConns(25)
	newDb.SetMaxIdleConns(5)
	newDb.SetConnMaxLifetime(time.Hour)

	s.db = newDb
	s.closed = false
	return nil
}

// Delete deletes a session from SQLite (public version)
func (s *SQLiteStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// GetAllSessions returns all sessions in the database for this provider
func (s *SQLiteStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	logger := log.WithFields(log.Fields{
		"component": "SQLiteStore",
		"method":    "GetAllSessions",
	})

	s.mu.RLock()
	defer s.mu.RUnlock()

	rows, err := s.db.QueryContext(ctx, `
		SELECT session_key, data FROM authentik_outposts_proxysession 
		WHERE provider_id = ? AND (expires IS NULL OR expires > datetime('now'))
	`, s.BaseStore.ProviderID())
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []*sessions.Session
	for rows.Next() {
		var sessionKey string
		var data []byte
		if err := rows.Scan(&sessionKey, &data); err != nil {
			return nil, err
		}

		// Remove prefix from session key
		sessionID := strings.TrimPrefix(sessionKey, s.GetKeyPrefix())
		session := sessions.NewSession(s, "")
		session.ID = sessionID

		if err := s.GetSerializer().Deserialize(data, session); err != nil {
			logger.WithError(err).WithField("session_id", sessionID).Warning("Failed to deserialize session")
			continue
		}
		result = append(result, session)
	}

	return result, rows.Err()
}

// StartPeriodicCleanup starts a background goroutine for periodic cleanup
func (s *SQLiteStore) StartPeriodicCleanup(ctx context.Context, cleanupInterval int) {
	if cleanupInterval <= 0 {
		cleanupInterval = 3600 // Default to hourly cleanup
	}

	logger := log.WithFields(log.Fields{
		"component":        "SQLiteStore",
		"method":           "StartPeriodicCleanup",
		"interval_seconds": cleanupInterval,
	})

	logger.Info("Starting periodic cleanup of expired sessions")

	ticker := time.NewTicker(time.Duration(cleanupInterval) * time.Second)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				if _, err := s.CleanupExpired(ctx); err != nil {
					logger.WithError(err).Warning("Failed to clean up expired sessions")
				}
			case <-ctx.Done():
				logger.Info("Stopping periodic cleanup of expired sessions")
				return
			}
		}
	}()
}

// CleanupExpired deletes expired sessions and returns the count
func (s *SQLiteStore) CleanupExpired(ctx context.Context) (int64, error) {
	logger := log.WithField("component", "SQLiteStore").WithField("method", "CleanupExpired")

	s.mu.RLock()
	defer s.mu.RUnlock()

	result, err := s.db.ExecContext(ctx, `
		DELETE FROM authentik_outposts_proxysession 
		WHERE expires <= datetime('now')
	`)
	if err != nil {
		return 0, err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return 0, err
	}

	if rowsAffected > 0 {
		logger.WithField("rows_affected", rowsAffected).Info("Expired sessions cleanup completed")
	}

	return rowsAffected, nil
}

// Additional methods to satisfy the interface
func (s *SQLiteStore) ProviderID() string {
	return s.BaseStore.ProviderID()
}

func (s *SQLiteStore) KeyPrefix() string {
	return s.GetKeyPrefix()
}
