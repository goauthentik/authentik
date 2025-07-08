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
	log "github.com/sirupsen/logrus"
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
	// cleanup interval
	cleanupInterval time.Duration
	// stop channel for cleanup goroutine
	stopCleanup chan bool
}

// KeyGenFunc defines a function used by store to generate a key
type KeyGenFunc func() (string, error)

// NewSQLiteStore returns a new SQLiteStore with default configuration
func NewSQLiteStore(dbPath string, cleanupInterval time.Duration) (*SQLiteStore, error) {
	// Ensure the directory exists
	dir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory for SQLite database: %w", err)
	}

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open SQLite database: %w", err)
	}

	// Create sessions table if it doesn't exist
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS sessions (
			id TEXT PRIMARY KEY,
			data BLOB,
			expiry DATETIME
		)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create sessions table: %w", err)
	}

	// Create index on expiry for efficient cleanup
	_, err = db.Exec(`
		CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expiry)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create expiry index: %w", err)
	}

	store := &SQLiteStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 86400 * 30,
		},
		keyPrefix:       "session:",
		keyGen:          generateRandomKey,
		serializer:      GobSerializer{},
		cleanupInterval: cleanupInterval,
		stopCleanup:     make(chan bool),
	}

	// Start cleanup goroutine
	go store.startCleanup()

	return store, nil
}

// Close closes the SQLite store and stops the cleanup goroutine
func (s *SQLiteStore) Close() error {
	s.stopCleanup <- true
	return s.db.Close()
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

	_, err = s.db.ExecContext(ctx, `
		INSERT INTO sessions (id, data, expiry) 
		VALUES (?, ?, ?) 
		ON CONFLICT(id) DO UPDATE SET data = excluded.data, expiry = excluded.expiry
	`, s.keyPrefix+session.ID, b, expiry)

	return err
}

// load reads session from SQLite
func (s *SQLiteStore) load(ctx context.Context, session *sessions.Session) error {
	var data []byte
	err := s.db.QueryRowContext(ctx, `
		SELECT data FROM sessions 
		WHERE id = ? AND (expiry IS NULL OR expiry > datetime('now'))
	`, s.keyPrefix+session.ID).Scan(&data)

	if err != nil {
		return err
	}

	return s.serializer.Deserialize(data, session)
}

// delete deletes session from SQLite
func (s *SQLiteStore) delete(ctx context.Context, session *sessions.Session) error {
	_, err := s.db.ExecContext(ctx, `DELETE FROM sessions WHERE id = ?`, s.keyPrefix+session.ID)
	return err
}

// Delete deletes a session from SQLite (public version of delete)
func (s *SQLiteStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// cleanup removes expired sessions from the database
func (s *SQLiteStore) cleanup() {
	_, err := s.db.Exec(`DELETE FROM sessions WHERE expiry <= datetime('now')`)
	if err != nil {
		log.WithError(err).Warning("failed to cleanup expired sessions")
	}
}

// startCleanup starts the cleanup goroutine which removes expired sessions periodically
func (s *SQLiteStore) startCleanup() {
	ticker := time.NewTicker(s.cleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.cleanup()
		case <-s.stopCleanup:
			return
		}
	}
}

// GetAllSessions returns all sessions in the database
func (s *SQLiteStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	rows, err := s.db.QueryContext(ctx, `
		SELECT id, data FROM sessions 
		WHERE (expiry IS NULL OR expiry > datetime('now'))
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
