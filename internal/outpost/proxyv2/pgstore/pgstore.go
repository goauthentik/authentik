package pgstore

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/sessionstore"
)

// PGStore stores gorilla sessions in PostgreSQL
type PGStore struct {
	*sessionstore.BaseStore
	// database connection
	db *sql.DB
	// schema to use for the sessions table
	schema string
}

// NewPGStore returns a new PGStore with default configuration
func NewPGStore(connStr string, schema string, providerID string, sessionOptions *sessions.Options) (*PGStore, error) {
	logger := log.WithFields(log.Fields{
		"component":   "PGStore",
		"schema":      schema,
		"provider_id": providerID,
	})

	logger.Debug("Creating new PostgreSQL store")

	// Connect to the database
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.WithError(err).Error("Failed to open PostgreSQL database")
		return nil, fmt.Errorf("failed to open PostgreSQL database: %w", err)
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		logger.WithError(err).Error("Failed to connect to PostgreSQL database")
		return nil, fmt.Errorf("failed to connect to PostgreSQL database: %w", err)
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
	store.BaseStore.KeyPrefix("authentik_proxy_session_")

	return store, nil
}

// Close closes the PostgreSQL store
func (s *PGStore) Close() error {
	logger := log.WithFields(log.Fields{
		"component": "PGStore",
		"schema":    s.schema,
	})

	logger.Debug("Closing PostgreSQL store")
	err := s.db.Close()
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
func (s *PGStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
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

// save writes session to PostgreSQL
func (s *PGStore) save(ctx context.Context, session *sessions.Session) error {
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

	// Use the new table and column names
	query := fmt.Sprintf(`
		INSERT INTO %s.authentik_outposts_proxysession (session_key, data, expires, expiring, provider_id) 
		VALUES ($1, $2, $3, $4, $5) 
		ON CONFLICT(session_key) DO UPDATE SET data = EXCLUDED.data, expires = EXCLUDED.expires
	`, s.schema)

	_, err = s.db.ExecContext(ctx, query, sessionKey, data, expiry, true, s.ProviderID())
	return err
}

// load reads session from PostgreSQL
func (s *PGStore) load(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("load", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)
	var data []byte

	query := fmt.Sprintf(`
		SELECT data FROM %s.authentik_outposts_proxysession 
		WHERE session_key = $1 AND (expires IS NULL OR expires > NOW())
	`, s.schema)

	err := s.db.QueryRowContext(ctx, query, sessionKey).Scan(&data)
	if err != nil {
		return err
	}

	return s.GetSerializer().Deserialize(data, session)
}

// delete deletes session from PostgreSQL
func (s *PGStore) delete(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		s.TrackOperation("delete", time.Since(start))
	}()

	sessionKey := s.GetSessionKey(session.ID)
	query := fmt.Sprintf(`DELETE FROM %s.authentik_outposts_proxysession WHERE session_key = $1`, s.schema)
	_, err := s.db.ExecContext(ctx, query, sessionKey)
	return err
}

// Delete deletes a session from PostgreSQL (public version)
func (s *PGStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// GetAllSessions returns all sessions in the database
func (s *PGStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	logger := log.WithFields(log.Fields{
		"component": "PGStore",
		"method":    "GetAllSessions",
		"schema":    s.schema,
	})

	query := fmt.Sprintf(`
		SELECT session_key, data FROM %s.authentik_outposts_proxysession 
		WHERE (expires IS NULL OR expires > NOW())
	`, s.schema)

	rows, err := s.db.QueryContext(ctx, query)
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
