package sessionstore

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/base32"
	"encoding/gob"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/sessions"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/proxyv2/metrics"
)

// SessionStore defines the interface for session storage backends
type SessionStore interface {
	sessions.Store
	Close() error
	Delete(ctx context.Context, session *sessions.Session) error
	GetAllSessions(ctx context.Context) ([]*sessions.Session, error)
	Options(opts sessions.Options)
	KeyPrefix(keyPrefix string)
	KeyGen(f KeyGenFunc)
	Serializer(ss SessionSerializer)
}

// KeyGenFunc defines a function used by store to generate a key
type KeyGenFunc func() (string, error)

// SessionSerializer provides an interface for serialize/deserialize a session
type SessionSerializer interface {
	Serialize(s *sessions.Session) ([]byte, error)
	Deserialize(b []byte, s *sessions.Session) error
}

// BaseStore contains common functionality for all session stores
type BaseStore struct {
	// default options to use when a new session is created
	options sessions.Options
	// key prefix with which the session will be stored
	keyPrefix string
	// key generator
	keyGen KeyGenFunc
	// session serializer
	serializer SessionSerializer
	// provider UUID to associate with sessions
	providerID string
	// store type for metrics
	storeType string
}

// NewBaseStore creates a new base store with default values
func NewBaseStore(providerID, storeType string) *BaseStore {
	return &BaseStore{
		options: sessions.Options{
			Path:   "/",
			MaxAge: 86400 * 30,
		},
		keyPrefix:  "session:",
		keyGen:     GenerateRandomKey,
		serializer: GobSerializer{},
		providerID: providerID,
		storeType:  storeType,
	}
}

// Options sets options to use when a new session is created
func (bs *BaseStore) Options(opts sessions.Options) {
	log.WithFields(log.Fields{
		"component": "BaseStore",
		"method":    "Options",
		"http_only": opts.HttpOnly,
		"secure":    opts.Secure,
		"max_age":   opts.MaxAge,
		"path":      opts.Path,
		"domain":    opts.Domain,
		"same_site": opts.SameSite,
	}).Debug("Setting session options")
	bs.options = opts
}

// KeyPrefix sets the key prefix to store session
func (bs *BaseStore) KeyPrefix(keyPrefix string) {
	log.WithFields(log.Fields{
		"component":  "BaseStore",
		"method":     "KeyPrefix",
		"key_prefix": keyPrefix,
	}).Debug("Setting key prefix")
	bs.keyPrefix = keyPrefix
}

// KeyGen sets the key generator function
func (bs *BaseStore) KeyGen(f KeyGenFunc) {
	log.WithFields(log.Fields{
		"component": "BaseStore",
		"method":    "KeyGen",
	}).Debug("Setting key generator function")
	bs.keyGen = f
}

// Serializer sets the session serializer to store session
func (bs *BaseStore) Serializer(ss SessionSerializer) {
	log.WithFields(log.Fields{
		"component": "BaseStore",
		"method":    "Serializer",
	}).Debug("Setting session serializer")
	bs.serializer = ss
}

// GetSessionKey returns the full session key with prefix
func (bs *BaseStore) GetSessionKey(sessionID string) string {
	return bs.keyPrefix + sessionID
}

// GetProviderID returns the provider ID
func (bs *BaseStore) ProviderID() string {
	return bs.providerID
}

// GetSerializer returns the session serializer
func (bs *BaseStore) GetSerializer() SessionSerializer {
	return bs.serializer
}

// GetKeyPrefix returns the key prefix
func (bs *BaseStore) GetKeyPrefix() string {
	return bs.keyPrefix
}

// CalculateExpiry calculates the expiry time for a session
func (bs *BaseStore) CalculateExpiry(session *sessions.Session) time.Time {
	if session.Options.MaxAge > 0 {
		return time.Now().Add(time.Duration(session.Options.MaxAge) * time.Second)
	}
	// If the MaxAge is 0 or negative then set expiry to now
	return time.Now()
}

// TrackOperation tracks metrics for session operations
func (bs *BaseStore) TrackOperation(operation string, duration time.Duration) {
	metrics.SessionDuration.With(prometheus.Labels{
		"outpost_name": "proxy", // TODO: Get actual outpost name
		"operation":    operation,
		"backend":      bs.storeType,
	}).Observe(duration.Seconds())

	metrics.SessionOperations.With(prometheus.Labels{
		"outpost_name": "proxy",
		"operation":    operation,
		"backend":      bs.storeType,
	}).Inc()
}

// HandleSessionSave handles common session save logic
func (bs *BaseStore) HandleSessionSave(w http.ResponseWriter, session *sessions.Session) error {
	// Delete if max-age is <= 0
	if session.Options.MaxAge <= 0 {
		log.WithFields(log.Fields{
			"component":    "BaseStore",
			"method":       "HandleSessionSave",
			"session_name": session.Name(),
			"session_id":   session.ID,
		}).Debug("Session max age <= 0, setting empty cookie to expire session")

		http.SetCookie(w, sessions.NewCookie(session.Name(), "", session.Options))
		return nil
	}

	// Generate session ID if needed
	if session.ID == "" {
		id, err := bs.keyGen()
		if err != nil {
			log.WithFields(log.Fields{
				"component":    "BaseStore",
				"method":       "HandleSessionSave",
				"session_name": session.Name(),
			}).WithError(err).Error("Failed to generate session ID")
			return err
		}
		session.ID = id
		log.WithFields(log.Fields{
			"component":      "BaseStore",
			"method":         "HandleSessionSave",
			"session_name":   session.Name(),
			"new_session_id": id,
		}).Debug("Generated new session ID")
	}

	// Set session cookie
	http.SetCookie(w, sessions.NewCookie(session.Name(), session.ID, session.Options))
	return nil
}

// CreateNewSession creates a new session with common setup
func (bs *BaseStore) CreateNewSession(store sessions.Store, r *http.Request, name string) (*sessions.Session, error) {
	logger := log.WithFields(log.Fields{
		"component":    "BaseStore",
		"method":       "CreateNewSession",
		"session_name": name,
		"request_path": r.URL.Path,
	})

	logger.Debug("Creating new session")
	session := sessions.NewSession(store, name)
	opts := bs.options
	session.Options = &opts
	session.IsNew = true

	c, err := r.Cookie(name)
	if err != nil {
		logger.WithError(err).Debug("No cookie found for session, returning new session")
		return session, nil
	}

	logger.WithField("cookie_value", c.Value).Debug("Found cookie for session")
	session.ID = c.Value
	return session, nil
}

// Gob serializer
type GobSerializer struct{}

func init() {
	// register common map tyles to prevent serialization errors
	gob.Register(map[string]string{})
	gob.Register(map[string]interface{}{})
	gob.Register(map[interface{}]interface{}{})
	gob.Register(map[string]int{})
	gob.Register(map[string]bool{})
	gob.Register(map[string]float64{})
	gob.Register([]interface{}{})
	gob.Register([]string{})
}

func (gs GobSerializer) Serialize(s *sessions.Session) ([]byte, error) {
	logger := log.WithFields(log.Fields{
		"component": "GobSerializer",
		"method":    "Serialize",
	})

	logger.Debug("Serializing session")
	buf := new(bytes.Buffer)
	enc := gob.NewEncoder(buf)
	err := enc.Encode(s.Values)
	if err == nil {
		logger.WithField("size", buf.Len()).Debug("Session serialized successfully")
		return buf.Bytes(), nil
	}
	logger.WithError(err).Error("Failed to serialize session")
	return nil, err
}

func (gs GobSerializer) Deserialize(d []byte, s *sessions.Session) error {
	logger := log.WithFields(log.Fields{
		"component": "GobSerializer",
		"method":    "Deserialize",
		"data_size": len(d),
	})

	logger.Debug("Deserializing session")
	dec := gob.NewDecoder(bytes.NewBuffer(d))
	err := dec.Decode(&s.Values)
	if err != nil {
		logger.WithError(err).Error("Failed to deserialize session")
	} else {
		logger.WithField("values_count", len(s.Values)).Debug("Session deserialized successfully")
	}
	return err
}

// GenerateRandomKey returns a new random key
func GenerateRandomKey() (string, error) {
	logger := log.WithField("component", "GenerateRandomKey")
	logger.Debug("Generating random key")

	k := make([]byte, 64)
	if _, err := io.ReadFull(rand.Reader, k); err != nil {
		logger.WithError(err).Error("Failed to generate random key")
		return "", err
	}
	key := strings.TrimRight(base32.StdEncoding.EncodeToString(k), "=")
	logger.WithField("key_length", len(key)).Debug("Random key generated")
	return key, nil
}
