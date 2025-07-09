package sqlitestore

import (
	"bytes"
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/base32"
	"encoding/gob"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/mattn/go-sqlite3"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
)

// SQLiteStore stores gorilla sessions in SQLite
type SQLiteStore struct {
	// database connection
	db *sql.DB
	// default options to use when a new session is created
	options sessions.Options
	// key prefix with which the session will be stored
	keyPrefix string
	// key generator
	keyGen KeyGenFunc
	// session serializer
	serializer SessionSerializer
	// path to the SQLite database file
	dbPath string
	// provider UUID to associate with sessions
	providerID string
}

// KeyGenFunc defines a function used by store to generate a key
type KeyGenFunc func() (string, error)

// NewSQLiteStore returns a new SQLiteStore with default configuration
func NewSQLiteStore(dbPath string, providerID string) (*SQLiteStore, error) {
	// Ensure the directory exists
	dir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory for SQLite database: %w", err)
	}

	// Create a new SQLite database
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open SQLite database: %w", err)
	}

	// Create sessions table with schema matching Django model in authentik/outposts/models.py:496
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS authentik_outposts_proxysession (
			uuid TEXT PRIMARY KEY,
			session_key TEXT UNIQUE,
			data BLOB,
			expires DATETIME,
			expiring BOOLEAN DEFAULT 1,
			provider_id TEXT,
			claims TEXT DEFAULT '{}',
			redirect TEXT DEFAULT ''
		)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create sessions table: %w", err)
	}

	// Create index on expires for efficient queries
	_, err = db.Exec(`
		CREATE INDEX IF NOT EXISTS idx_proxysession_expires ON authentik_outposts_proxysession(expires)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create expiry index: %w", err)
	}

	// Create index on session_key for efficient lookups
	_, err = db.Exec(`
		CREATE INDEX IF NOT EXISTS idx_proxysession_session_key ON authentik_outposts_proxysession(session_key)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create session_key index: %w", err)
	}

	store := &SQLiteStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 86400 * 30,
		},
		keyPrefix:  "session:",
		keyGen:     generateRandomKey,
		serializer: GobSerializer{},
		dbPath:     dbPath,
		providerID: providerID,
	}

	return store, nil
}

// Close closes the SQLite store
func (s *SQLiteStore) Close() error {
	err := s.db.Close()

	// Attempt to remove the database file if it's in a temp directory
	if strings.Contains(s.dbPath, os.TempDir()) {
		if rmErr := os.Remove(s.dbPath); rmErr != nil {
			log.WithError(rmErr).Warning("failed to remove temporary SQLite database")
		} else {
			log.WithField("path", s.dbPath).Info("Removed temporary SQLite database")
		}
	}

	return err
}

// Get returns a session for the given name after adding it to the registry.
func (s *SQLiteStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry.
func (s *SQLiteStore) New(r *http.Request, name string) (*sessions.Session, error) {
	session := sessions.NewSession(s, name)
	opts := s.options
	session.Options = &opts
	session.IsNew = true

	c, err := r.Cookie(name)
	if err != nil {
		return session, nil
	}
	session.ID = c.Value

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

// Save adds a single session to the response.
//
// If the Options.MaxAge of the session is <= 0 then the session will be
// deleted from the store. with this process it enforces the properly
// session cookie handling so no need to trust in the cookie management in the
// web browser.
func (s *SQLiteStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Delete if max-age is <= 0
	if session.Options.MaxAge <= 0 {
		if err := s.delete(r.Context(), session); err != nil {
			return err
		}
		http.SetCookie(w, sessions.NewCookie(session.Name(), "", session.Options))
		return nil
	}

	if session.ID == "" {
		id, err := s.keyGen()
		if err != nil {
			return errors.New("sqlitestore: failed to generate session id")
		}
		session.ID = id
	}
	if err := s.save(r.Context(), session); err != nil {
		return err
	}

	http.SetCookie(w, sessions.NewCookie(session.Name(), session.ID, session.Options))
	return nil
}

// Options set options to use when a new session is created
func (s *SQLiteStore) Options(opts sessions.Options) {
	s.options = opts
}

// KeyPrefix sets the key prefix to store session in SQLite
func (s *SQLiteStore) KeyPrefix(keyPrefix string) {
	s.keyPrefix = keyPrefix
}

// KeyGen sets the key generator function
func (s *SQLiteStore) KeyGen(f KeyGenFunc) {
	s.keyGen = f
}

// Serializer sets the session serializer to store session
func (s *SQLiteStore) Serializer(ss SessionSerializer) {
	s.serializer = ss
}

// save writes session in SQLite
func (s *SQLiteStore) save(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		duration := time.Since(start).Seconds()
		metrics.SessionDuration.With(prometheus.Labels{
			"outpost_name": "proxy", // TODO: Get actual outpost name
			"operation":    "save",
			"backend":      "sqlite",
		}).Observe(duration)
		metrics.SessionOperations.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "save",
			"backend":      "sqlite",
		}).Inc()
	}()

	b, err := s.serializer.Serialize(session)
	if err != nil {
		return err
	}

	// Calculate expiry time based on MaxAge of the cookie
	var expiry time.Time
	if session.Options.MaxAge > 0 {
		expiry = time.Now().Add(time.Duration(session.Options.MaxAge) * time.Second)
	} else {
		// If the MaxAge is 0 or negative then set expiry to now which will
		// ensure it gets cleaned up
		expiry = time.Now()
	}

	// Generate a UUID for the session if it doesn't exist
	uuid, err := generateRandomKey()
	if err != nil {
		return err
	}

	sessionKey := s.keyPrefix + session.ID

	// Extract claims and redirect from session if they exist
	claims := "{}"
	if c, ok := session.Values["claims"]; ok && c != nil {
		claims = fmt.Sprintf("%v", c)
	}

	redirect := ""
	if r, ok := session.Values["redirect"]; ok && r != nil {
		redirect = fmt.Sprintf("%v", r)
	}

	_, err = s.db.ExecContext(ctx, `
		INSERT INTO authentik_outposts_proxysession (
			uuid, session_key, data, expires, expiring, provider_id, claims, redirect
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(session_key) DO UPDATE SET 
			data = excluded.data, 
			expires = excluded.expires, 
			claims = excluded.claims,
			redirect = excluded.redirect
	`, uuid, sessionKey, b, expiry, true, s.providerID, claims, redirect)

	return err
}

// load reads session from SQLite
func (s *SQLiteStore) load(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		duration := time.Since(start).Seconds()
		metrics.SessionDuration.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "load",
			"backend":      "sqlite",
		}).Observe(duration)
		metrics.SessionOperations.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "load",
			"backend":      "sqlite",
		}).Inc()
	}()

	var data []byte
	err := s.db.QueryRowContext(ctx, `
		SELECT data FROM authentik_outposts_proxysession 
		WHERE session_key = ? AND (expires IS NULL OR expires > datetime('now'))
	`, s.keyPrefix+session.ID).Scan(&data)

	if err != nil {
		return err
	}

	return s.serializer.Deserialize(data, session)
}

// delete deletes session from SQLite
func (s *SQLiteStore) delete(ctx context.Context, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		duration := time.Since(start).Seconds()
		metrics.SessionDuration.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "delete",
			"backend":      "sqlite",
		}).Observe(duration)
		metrics.SessionOperations.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "delete",
			"backend":      "sqlite",
		}).Inc()
	}()

	_, err := s.db.ExecContext(ctx, `DELETE FROM authentik_outposts_proxysession WHERE session_key = ?`, s.keyPrefix+session.ID)
	return err
}

// Delete deletes a session from SQLite (public version of delete)
func (s *SQLiteStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// GetAllSessions returns all sessions in the database
func (s *SQLiteStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT session_key, data FROM authentik_outposts_proxysession 
		WHERE (expires IS NULL OR expires > datetime('now'))
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []*sessions.Session
	for rows.Next() {
		var id string
		var data []byte
		if err := rows.Scan(&id, &data); err != nil {
			return nil, err
		}

		// Remove prefix from ID
		id = strings.TrimPrefix(id, s.keyPrefix)

		session := sessions.NewSession(s, "")
		session.ID = id
		if err := s.serializer.Deserialize(data, session); err != nil {
			log.WithError(err).Warning("failed to deserialize session")
			continue
		}
		result = append(result, session)
	}

	return result, nil
}

// SessionSerializer provides an interface for serialize/deserialize a session
type SessionSerializer interface {
	Serialize(s *sessions.Session) ([]byte, error)
	Deserialize(b []byte, s *sessions.Session) error
}

// Gob serializer
type GobSerializer struct{}

func (gs GobSerializer) Serialize(s *sessions.Session) ([]byte, error) {
	buf := new(bytes.Buffer)
	enc := gob.NewEncoder(buf)
	err := enc.Encode(s.Values)
	if err == nil {
		return buf.Bytes(), nil
	}
	return nil, err
}

func (gs GobSerializer) Deserialize(d []byte, s *sessions.Session) error {
	dec := gob.NewDecoder(bytes.NewBuffer(d))
	return dec.Decode(&s.Values)
}

// generateRandomKey returns a new random key
func generateRandomKey() (string, error) {
	k := make([]byte, 64)
	if _, err := io.ReadFull(rand.Reader, k); err != nil {
		return "", err
	}
	return strings.TrimRight(base32.StdEncoding.EncodeToString(k), "="), nil
}

func (s *SQLiteStore) DB() *sql.DB {
	return s.db
}

// CleanupExpired deletes all expired sessions from the database
func (s *SQLiteStore) CleanupExpired(ctx context.Context) (int64, error) {
	start := time.Now()
	defer func(start time.Time) {
		duration := time.Since(start).Seconds()
		metrics.SessionDuration.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "cleanup",
			"backend":      "sqlite",
		}).Observe(duration)
		metrics.SessionOperations.With(prometheus.Labels{
			"outpost_name": "proxy",
			"operation":    "cleanup",
			"backend":      "sqlite",
		}).Inc()
	}(start)

	result, err := s.db.ExecContext(ctx, `DELETE FROM authentik_outposts_proxysession WHERE expires IS NOT NULL AND expires < datetime('now')`)
	if err != nil {
		return 0, err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return 0, err
	}

	metrics.SessionCleanupTotal.With(prometheus.Labels{
		"outpost_name": "proxy",
		"backend":      "sqlite",
	}).Add(float64(rowsAffected))

	return rowsAffected, nil
}
