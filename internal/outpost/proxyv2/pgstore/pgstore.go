package pgstore

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

// PGStore stores gorilla sessions in PostgreSQL
type PGStore struct {
	*sessionstore.BaseStore
	// database connection
	db *gorm.DB
	// schema to use for the sessions table
	schema string
}

// GetDB returns the gorm DB
func (s *PGStore) GetDB() *gorm.DB {
	return s.db
}

// NowValue returns the function to get the current time in the database
func (s *PGStore) NowValue() string {
	return "NOW()"
}

// NewPGStore returns a new PGStore with default configuration
func NewPGStore(connStr string, schema string, providerID string, sessionOptions *sessions.Options) (*PGStore, error) {
	logger := log.WithFields(log.Fields{
		"component":   "PGStore",
		"schema":      schema,
		"provider_id": providerID,
	})

	logger.Debug("Creating new PostgreSQL store")

	// Configure GORM logger
	gormLogLevel := gormlogger.Silent
	if log.GetLevel() == log.DebugLevel {
		gormLogLevel = gormlogger.Info
	}

	gormConfig := gormlogger.Config{
		SlowThreshold:             time.Second,
		LogLevel:                  gormLogLevel,
		IgnoreRecordNotFoundError: true,
		Colorful:                  false,
	}

	gormLogger := gormlogger.New(
		log.StandardLogger(),
		gormConfig,
	)

	// Connect to the database
	sqlDB, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.WithError(err).Error("Failed to open PostgreSQL database")
		return nil, fmt.Errorf("failed to open PostgreSQL database: %w", err)
	}

	// Verify connection
	if err := sqlDB.Ping(); err != nil {
		sqlDB.Close()
		logger.WithError(err).Error("Failed to connect to PostgreSQL database")
		return nil, fmt.Errorf("failed to connect to PostgreSQL database: %w", err)
	}

	// Create GORM DB instance
	db, err := gorm.Open(postgres.New(postgres.Config{
		Conn: sqlDB,
	}), &gorm.Config{
		Logger: gormLogger,
	})
	if err != nil {
		sqlDB.Close()
		logger.WithError(err).Error("Failed to create GORM instance")
		return nil, fmt.Errorf("failed to create GORM instance: %w", err)
	}

	// Set schema if provided
	if schema != "" && schema != "public" {
		db = db.Table(schema + ".authentik_outposts_proxysession")
	}

	logger.Debug("PostgreSQL store successfully initialized")
	store := &PGStore{
		BaseStore: sessionstore.NewBaseStore(providerID, "postgres"),
		db:        db,
		schema:    schema,
	}

	// Configure session options if provided
	if sessionOptions != nil {
		store.BaseStore.Options(*sessionOptions)
	}

	// Set key prefix for PostgreSQL sessions
	store.BaseStore.KeyPrefix("authentik_proxy_")

	return store, nil
}

// Close closes the PostgreSQL store
func (s *PGStore) Close() error {
	logger := log.WithFields(log.Fields{
		"component": "PGStore",
		"schema":    s.schema,
	})

	logger.Debug("Closing PostgreSQL store")
	sqlDB, err := s.db.DB()
	if err != nil {
		logger.WithError(err).Error("Error getting SQL DB from GORM")
		return err
	}

	err = sqlDB.Close()
	if err != nil {
		logger.WithError(err).Error("Error closing PostgreSQL database connection")
	} else {
		logger.Debug("PostgreSQL store closed successfully")
	}
	return err
}

// Get returns a session for the given name after adding it to the registry
func (s *PGStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry
func (s *PGStore) New(r *http.Request, name string) (*sessions.Session, error) {
	session, err := s.CreateNewSession(s, r, name)
	if err != nil {
		return session, err
	}

	if session.ID == "" {
		return session, nil
	}

	// Load session data from store
	err = s.BaseStore.Load(r.Context(), s, session)
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
func (s *PGStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Handle common save logic (cookie management, ID generation)
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

// Delete deletes a session from PostgreSQL (public version)
func (s *PGStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.BaseStore.Delete(ctx, s, session)
}

// GetAllSessions returns all sessions in the database
func (s *PGStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	return s.BaseStore.GetAllSessions(ctx, s)
}

// CleanupExpiredSessions removes expired sessions and old soft-deleted sessions from PostgreSQL
func (s *PGStore) CleanupExpiredSessions() error {
	logger := log.WithFields(log.Fields{
		"component": "PGStore",
		"schema":    s.schema,
		"method":    "cleanup",
	})

	start := time.Now()
	defer func() {
		s.TrackOperation("cleanup", time.Since(start))
	}()

	now := time.Now()

	// Hard delete expired sessions
	result := s.db.Where("expires < ? AND expires IS NOT NULL", now).Delete(&sessionstore.ProxySession{})

	if result.Error != nil {
		logger.WithError(result.Error).Warning("Failed to delete expired sessions")
		return result.Error
	}

	logger.WithField("deleted_count", result.RowsAffected).Debug("Deleted expired sessions")

	// Hard delete old soft-deleted sessions (older than 30 days)
	oldSoftDeleteCutoff := now.AddDate(0, 0, -30)
	softDeleteResult := s.db.Unscoped().Where("deleted_at IS NOT NULL AND deleted_at < ?", oldSoftDeleteCutoff).Delete(&sessionstore.ProxySession{})

	if softDeleteResult.Error != nil {
		logger.WithError(softDeleteResult.Error).Warning("Failed to cleanup old soft-deleted sessions")
		return softDeleteResult.Error
	}

	if softDeleteResult.RowsAffected > 0 {
		logger.WithField("deleted_count", softDeleteResult.RowsAffected).Debug("Cleaned up old soft-deleted sessions")
	}

	return nil
}
