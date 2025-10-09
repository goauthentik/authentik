package postgresstore

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/mitchellh/mapstructure"
	log "github.com/sirupsen/logrus"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// PostgresStore stores gorilla sessions in PostgreSQL using GORM
type PostgresStore struct {
	db *gorm.DB
	// default options to use when a new session is created
	options sessions.Options
	// key prefix with which the session will be stored
	keyPrefix string
	log       *log.Entry
}

// ProxySession represents the session data structure in PostgreSQL
type ProxySession struct {
	UUID        uuid.UUID  `gorm:"type:uuid;primaryKey;column:uuid;default:gen_random_uuid()"`
	SessionKey  string     `gorm:"column:session_key"`
	UserID      *uuid.UUID `gorm:"column:user_id"`
	SessionData string     `gorm:"type:jsonb;column:session_data"`
	Expires     time.Time  `gorm:"column:expires"`
	Expiring    bool       `gorm:"column:expiring"`
}

// TableName specifies the table name for GORM
func (ProxySession) TableName() string {
	return "authentik_providers_proxy_proxysession"
}

// BuildDSN constructs a PostgreSQL connection string
func BuildDSN(cfg config.PostgreSQLConfig) (string, error) {
	// Validate required fields
	if cfg.Host == "" {
		return "", fmt.Errorf("PostgreSQL host is required")
	}
	if cfg.User == "" {
		return "", fmt.Errorf("PostgreSQL user is required")
	}
	if cfg.Name == "" {
		return "", fmt.Errorf("PostgreSQL database name is required")
	}
	if cfg.Port <= 0 {
		return "", fmt.Errorf("PostgreSQL port must be positive")
	}

	// Build DSN string with all parameters
	dsnParts := []string{
		"host=" + cfg.Host,
		fmt.Sprintf("port=%d", cfg.Port),
		"user=" + cfg.User,
		"dbname=" + cfg.Name,
	}

	if cfg.Password != "" {
		dsnParts = append(dsnParts, "password="+cfg.Password)
	}

	// Add SSL mode
	if cfg.SSLMode != "" {
		dsnParts = append(dsnParts, "sslmode="+cfg.SSLMode)
	} else {
		dsnParts = append(dsnParts, "sslmode=prefer")
	}

	// Add SSL certificates if provided
	if cfg.SSLRootCert != "" {
		dsnParts = append(dsnParts, "sslrootcert="+cfg.SSLRootCert)
	}
	if cfg.SSLCert != "" {
		dsnParts = append(dsnParts, "sslcert="+cfg.SSLCert)
	}
	if cfg.SSLKey != "" {
		dsnParts = append(dsnParts, "sslkey="+cfg.SSLKey)
	}
	if cfg.DefaultSchema != "" {
		dsnParts = append(dsnParts, "search_path="+cfg.DefaultSchema)
	}

	// Add connection options if specified
	if cfg.ConnOptions != "" {
		dsnParts = append(dsnParts, cfg.ConnOptions)
	}

	// Join parts with spaces
	return strings.Join(dsnParts, " "), nil
}

// NewPostgresStore returns a new PostgresStore
func NewPostgresStore() (*PostgresStore, error) {
	cfg := config.Get().PostgreSQL

	// Build connection string
	dsn, err := BuildDSN(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to build DSN: %w", err)
	}

	// Configure GORM
	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	}

	db, err := gorm.Open(postgres.Open(dsn), gormConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to PostgreSQL: %w", err)
	}

	// Configure connection pool
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get underlying sql.DB: %w", err)
	}

	// Set connection pool settings
	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetMaxOpenConns(100)

	if cfg.ConnMaxAge > 0 {
		sqlDB.SetConnMaxLifetime(time.Duration(cfg.ConnMaxAge) * time.Second)
	} else {
		sqlDB.SetConnMaxLifetime(time.Hour) // Default 1 hour
	}

	ps := &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 86400 * 30, // 30 days default (but overwritten in postgresstore creation based on token validation)
		},
		keyPrefix: "authentik_proxy_session_",
		log:       log.WithField("logger", "authentik.outpost.proxyv2.postgresstore"),
	}

	return ps, nil
}

// Get returns a session for the given name after adding it to the registry.
func (s *PostgresStore) Get(r *http.Request, name string) (*sessions.Session, error) {
	return sessions.GetRegistry(r).Get(s, name)
}

// New returns a session for the given name without adding it to the registry.
func (s *PostgresStore) New(r *http.Request, name string) (*sessions.Session, error) {
	session := sessions.NewSession(s, name)
	opts := s.options
	session.Options = &opts
	session.IsNew = true

	c, err := r.Cookie(name)
	if err != nil {
		return session, nil
	}
	session.ID = c.Value

	err = s.load(session)
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return session, nil
		}
		return session, err
	}
	session.IsNew = false
	return session, err
}

// Save adds a single session to the response.
func (s *PostgresStore) Save(r *http.Request, w http.ResponseWriter, session *sessions.Session) error {
	// Delete if max-age is <= 0
	if session.Options.MaxAge <= 0 {
		if err := s.delete(session); err != nil {
			return err
		}
		http.SetCookie(w, sessions.NewCookie(session.Name(), "", session.Options))
		return nil
	}

	if session.ID == "" {
		// Generate new session ID
		session.ID = s.keyPrefix + generateSessionID()
	}

	if err := s.save(session); err != nil {
		return err
	}

	http.SetCookie(w, sessions.NewCookie(session.Name(), session.ID, session.Options))
	return nil
}

// Options set options to use when a new session is created
func (s *PostgresStore) Options(opts sessions.Options) {
	s.options = opts
}

// KeyPrefix sets the key prefix to store session in PostgreSQL
func (s *PostgresStore) KeyPrefix(keyPrefix string) {
	s.keyPrefix = keyPrefix
}

// Close closes the PostgreSQL store
func (s *PostgresStore) Close() error {
	sqlDB, err := s.db.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// save writes session to PostgreSQL
func (s *PostgresStore) save(session *sessions.Session) error {
	// Convert session.Values (map[interface{}]interface{}) to map[string]interface{} for JSON marshaling
	stringKeyedValues := make(map[string]interface{})
	for k, v := range session.Values {
		if key, ok := k.(string); ok {
			stringKeyedValues[key] = v
		}
	}

	// Serialize all session values to JSON
	sessionData, err := json.Marshal(stringKeyedValues)
	if err != nil {
		return fmt.Errorf("failed to marshal session values: %w", err)
	}

	// Extract user ID from claims if it exists
	var userID *uuid.UUID
	if claims, hasClaims := session.Values[constants.SessionClaims]; hasClaims {
		if claimsMap, ok := claims.(map[string]interface{}); ok {
			if sub, exists := claimsMap["sub"]; exists {
				if subStr, ok := sub.(string); ok {
					if parsedUUID, err := uuid.Parse(subStr); err == nil {
						userID = &parsedUUID
					}
				}
			}
		}
	}

	proxySession := ProxySession{
		UUID:        uuid.New(),
		SessionKey:  session.ID,
		UserID:      userID,
		SessionData: string(sessionData),
	}

	// Add expiration timestamp to session data
	if session.Options != nil && session.Options.MaxAge > 0 {
		expiresAt := time.Now().UTC().Add(time.Duration(session.Options.MaxAge) * time.Second)
		proxySession.Expires = expiresAt
	}

	return s.db.Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "session_key"}},
		DoUpdates: clause.AssignmentColumns([]string{"user_id", "session_data"}),
	}).Create(&proxySession).Error
}

// load reads session from PostgreSQL
func (s *PostgresStore) load(session *sessions.Session) error {
	var proxySession ProxySession
	err := s.db.Where("session_key = ?", session.ID).First(&proxySession).Error

	if err != nil {
		return err
	}

	// Check if session is expired
	if time.Now().UTC().After(proxySession.Expires) {
		// Session is expired, delete it and return not found error
		s.db.Delete(&ProxySession{}, "session_key = ?", session.ID)
		return gorm.ErrRecordNotFound
	}

	// Deserialize session data from JSON
	if proxySession.SessionData != "" && proxySession.SessionData != "{}" {
		// First unmarshal to map[string]interface{}
		var stringKeyedValues map[string]interface{}
		err = json.Unmarshal([]byte(proxySession.SessionData), &stringKeyedValues)
		if err != nil {
			return fmt.Errorf("failed to unmarshal session data: %w", err)
		}

		// Convert back to map[interface{}]interface{} for gorilla/sessions compatibility
		session.Values = make(map[interface{}]interface{})
		for k, v := range stringKeyedValues {
			session.Values[k] = v
		}
	}

	return nil
}

// delete removes session from PostgreSQL
func (s *PostgresStore) delete(session *sessions.Session) error {
	return s.db.Delete(&ProxySession{}, "session_key = ?", session.ID).Error
}

// CleanupExpired removes expired sessions by checking MaxAge in session_data
func (s *PostgresStore) CleanupExpired() error {
	result := s.db.Where(`"expires" < ?`, time.Now().UTC().Format(time.RFC3339)).Delete(&ProxySession{})
	if result.Error != nil {
		return fmt.Errorf("failed to delete expired sessions: %w", result.Error)
	}

	if result.RowsAffected > 0 {
		s.log.WithField("count", result.RowsAffected).Info("Cleaned up expired sessions")
	}

	return nil
}

// LogoutSessions removes sessions that match the given filter criteria
// The filter function should return true for sessions that should be deleted
func (s *PostgresStore) LogoutSessions(ctx context.Context, filter func(c types.Claims) bool) error {
	// First, try to use JSONB operators for common filter patterns to avoid N+1 queries
	// If the filter is too complex, fall back to client-side filtering

	// Pre-filter sessions using JSONB operators where possible
	// Only fetch sessions that have claims (session_data->'claims' IS NOT NULL)
	var sessions []ProxySession
	err := s.db.Where(fmt.Sprintf("session_data::jsonb ? '%s'", constants.SessionClaims)).Find(&sessions).Error
	if err != nil {
		return fmt.Errorf("failed to fetch sessions: %w", err)
	}

	var sessionKeysToDelete []string

	for _, session := range sessions {
		if session.SessionData == "" || session.SessionData == "{}" {
			continue
		}

		var sessionData map[string]interface{}
		if err := json.Unmarshal([]byte(session.SessionData), &sessionData); err != nil {
			continue
		}

		claimsData, hasClaims := sessionData[constants.SessionClaims]
		if !hasClaims {
			continue
		}

		claimsMap, ok := claimsData.(map[string]interface{})
		if !ok {
			continue
		}

		// Only decode Sub and Sid fields since those are the only ones used in filters
		var claims types.Claims
		if err := mapstructure.Decode(claimsMap, &claims); err != nil {
			continue
		}

		if filter(claims) {
			sessionKeysToDelete = append(sessionKeysToDelete, session.SessionKey)
		}
	}

	if len(sessionKeysToDelete) > 0 {
		err = s.db.Delete(&ProxySession{}, "session_key IN ?", sessionKeysToDelete).Error
		if err != nil {
			return fmt.Errorf("failed to delete sessions: %w", err)
		}
	}

	return nil
}

// generateSessionID generates a random session ID
func generateSessionID() string {
	return uuid.New().String()
}

var (
	globalStore *PostgresStore
	mu          sync.Mutex
)

// GetPersistentStore creates a new postgres store if it is the first time the function has been called.
// If the function is called multiple times, the store from the variable is returned to ensure that only one instance is running.
func GetPersistentStore() (*PostgresStore, error) {
	mu.Lock()
	defer mu.Unlock()

	if globalStore == nil {
		store, err := NewPostgresStore()
		if err != nil {
			return nil, err
		}
		globalStore = store
	}

	return globalStore, nil
}

// StopPersistentStore stops the cleanup background job and clears the globalStore variable.
func StopPersistentStore() {
	mu.Lock()
	defer mu.Unlock()

	if globalStore != nil {
		_ = globalStore.Close()
		globalStore = nil
	}
}

// NewTestStore creates a PostgresStore for testing with the given database
func NewTestStore(db *gorm.DB) *PostgresStore {
	return &PostgresStore{
		db: db,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
		log:       log.WithField("logger", "test"),
	}
}
