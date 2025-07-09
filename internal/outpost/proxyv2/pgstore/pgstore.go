package pgstore

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/base32"
	"encoding/gob"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/sessions"
	_ "github.com/lib/pq"
)

// PGStore stores gorilla sessions in PostgreSQL
type PGStore struct {
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
	// schema to use for the sessions table
	schema string
	// provider UUID to associate with sessions
	providerID string
}

// KeyGenFunc defines a function used by store to generate a key
type KeyGenFunc func() (string, error)

// NewPGStore returns a new PGStore with default configuration
func NewPGStore(connStr string, schema string, providerID string) (*PGStore, error) {
	// Connect to the database without running migrations
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to open PostgreSQL database: %w", err)
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to connect to PostgreSQL database: %w", err)
	}

	// this thing feels repeated. could be moved in a common function
	store := &PGStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 86400 * 30,
		},
		keyPrefix:  "session:",
		keyGen:     generateRandomKey,
		serializer: GobSerializer{},
		schema:     schema,
		providerID: providerID,
	}

	return store, nil
}

// Close closes the PostgreSQL store
func (s *PGStore) Close() error {
	return s.db.Close()
}

// Get returns a session for the given name after adding it to the registry.
func (s *PGStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry.
func (s *PGStore) New(r *http.Request, name string) (*sessions.Session, error) {
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
func (s *PGStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
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
			return errors.New("pgstore: failed to generate session id")
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
func (s *PGStore) Options(opts sessions.Options) {
	s.options = opts
}

// KeyPrefix sets the key prefix to store session in PostgreSQL
func (s *PGStore) KeyPrefix(keyPrefix string) {
	s.keyPrefix = keyPrefix
}

// KeyGen sets the key generator function
func (s *PGStore) KeyGen(f KeyGenFunc) {
	s.keyGen = f
}

// Serializer sets the session serializer to store session
func (s *PGStore) Serializer(ss SessionSerializer) {
	s.serializer = ss
}

// save writes session in PostgreSQL
func (s *PGStore) save(ctx context.Context, session *sessions.Session) error {
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

	// Use the new table and column names
	_, err = s.db.ExecContext(ctx, fmt.Sprintf(`
		INSERT INTO %s.authentik_outposts_proxysession (session_key, data, expires, expiring, provider_id) 
		VALUES ($1, $2, $3, $4, $5) 
		ON CONFLICT(session_key) DO UPDATE SET data = EXCLUDED.data, expires = EXCLUDED.expires
	`, s.schema), s.keyPrefix+session.ID, b, expiry, true, s.providerID)

	return err
}

// load reads session from PostgreSQL
func (s *PGStore) load(ctx context.Context, session *sessions.Session) error {
	var data []byte
	err := s.db.QueryRowContext(ctx, fmt.Sprintf(`
		SELECT data FROM %s.authentik_outposts_proxysession 
		WHERE session_key = $1 AND (expires IS NULL OR expires > NOW())
	`, s.schema), s.keyPrefix+session.ID).Scan(&data)

	if err != nil {
		return err
	}

	return s.serializer.Deserialize(data, session)
}

// delete deletes session from PostgreSQL
func (s *PGStore) delete(ctx context.Context, session *sessions.Session) error {
	_, err := s.db.ExecContext(ctx, fmt.Sprintf(`DELETE FROM %s.authentik_outposts_proxysession WHERE session_key = $1`, s.schema), s.keyPrefix+session.ID)
	return err
}

// Delete deletes a session from PostgreSQL (public version of delete)
func (s *PGStore) Delete(ctx context.Context, session *sessions.Session) error {
	return s.delete(ctx, session)
}

// GetAllSessions returns all sessions from the store
func (s *PGStore) GetAllSessions(ctx context.Context) ([]*sessions.Session, error) {
	rows, err := s.db.QueryContext(ctx, fmt.Sprintf(`
		SELECT session_key, data FROM %s.authentik_outposts_proxysession 
		WHERE expires > NOW() OR expires IS NULL
	`, s.schema))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var result []*sessions.Session
	for rows.Next() {
		var id string
		var data []byte
		err = rows.Scan(&id, &data)
		if err != nil {
			return nil, err
		}

		if !strings.HasPrefix(id, s.keyPrefix) {
			continue
		}

		// Create a new session
		session := sessions.NewSession(s, "")
		session.ID = strings.TrimPrefix(id, s.keyPrefix)
		if err = s.serializer.Deserialize(data, session); err != nil {
			return nil, err
		}

		result = append(result, session)
	}

	return result, nil
}

// SessionSerializer interface for serializing/deserializing session data
type SessionSerializer interface {
	Serialize(s *sessions.Session) ([]byte, error)
	Deserialize(b []byte, s *sessions.Session) error
}

// GobSerializer uses gob package to encode/decode session data
type GobSerializer struct{}

func (gs GobSerializer) Serialize(s *sessions.Session) ([]byte, error) {
	buf := new(strings.Builder)
	enc := gob.NewEncoder(buf)
	err := enc.Encode(s.Values)
	if err != nil {
		return nil, err
	}
	return []byte(buf.String()), nil
}

func (gs GobSerializer) Deserialize(d []byte, s *sessions.Session) error {
	dec := gob.NewDecoder(strings.NewReader(string(d)))
	return dec.Decode(&s.Values)
}

func generateRandomKey() (string, error) {
	k := make([]byte, 32)
	if _, err := io.ReadFull(rand.Reader, k); err != nil {
		return "", err
	}
	return base32.StdEncoding.EncodeToString(k), nil
}
