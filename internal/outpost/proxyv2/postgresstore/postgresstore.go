package postgresstore

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/stdlib"
	"github.com/mitchellh/mapstructure"
	log "github.com/sirupsen/logrus"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

// PostgresStore stores gorilla sessions in PostgreSQL using GORM
type PostgresStore struct {
	db   *gorm.DB
	pool *RefreshableConnPool // Keep reference to pool for cleanup
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

// BuildConnConfig constructs a pgx.ConnConfig from PostgreSQL configuration.
func BuildConnConfig(cfg config.PostgreSQLConfig) (*pgx.ConnConfig, error) {
	// Validate required fields
	if cfg.Host == "" {
		return nil, fmt.Errorf("PostgreSQL host is required")
	}
	if cfg.User == "" {
		return nil, fmt.Errorf("PostgreSQL user is required")
	}
	if cfg.Name == "" {
		return nil, fmt.Errorf("PostgreSQL database name is required")
	}
	if cfg.Port <= 0 {
		return nil, fmt.Errorf("PostgreSQL port must be positive")
	}

	// Start with a default config
	connConfig, err := pgx.ParseConfig("")
	if err != nil {
		return nil, fmt.Errorf("failed to create default config: %w", err)
	}

	// Set connection parameters
	connConfig.Host = cfg.Host
	connConfig.Port = uint16(cfg.Port)
	connConfig.User = cfg.User
	connConfig.Password = cfg.Password
	connConfig.Database = cfg.Name

	// Configure TLS/SSL
	if cfg.SSLMode != "" {
		switch cfg.SSLMode {
		case "disable":
			connConfig.TLSConfig = nil
		case "require", "verify-ca", "verify-full":
			tlsConfig := &tls.Config{}

			// Load root CA certificate if provided
			if cfg.SSLRootCert != "" {
				caCert, err := os.ReadFile(cfg.SSLRootCert)
				if err != nil {
					return nil, fmt.Errorf("failed to read SSL root certificate: %w", err)
				}
				caCertPool := x509.NewCertPool()
				if !caCertPool.AppendCertsFromPEM(caCert) {
					return nil, fmt.Errorf("failed to parse SSL root certificate")
				}
				tlsConfig.RootCAs = caCertPool
			}

			// Load client certificate and key if provided
			if cfg.SSLCert != "" && cfg.SSLKey != "" {
				cert, err := tls.LoadX509KeyPair(cfg.SSLCert, cfg.SSLKey)
				if err != nil {
					return nil, fmt.Errorf("failed to load SSL client certificate: %w", err)
				}
				tlsConfig.Certificates = []tls.Certificate{cert}
			}

			// Set verification mode
			switch cfg.SSLMode {
			case "require":
				// Don't verify the server certificate (just encrypt)
				tlsConfig.InsecureSkipVerify = true
			case "verify-ca":
				// Verify the certificate is signed by a trusted CA
				tlsConfig.InsecureSkipVerify = false
			case "verify-full":
				// Verify the certificate and hostname
				tlsConfig.InsecureSkipVerify = false
				tlsConfig.ServerName = cfg.Host
			}

			connConfig.TLSConfig = tlsConfig
		}
	}

	// Set runtime params
	if connConfig.RuntimeParams == nil {
		connConfig.RuntimeParams = make(map[string]string)
	}

	if cfg.DefaultSchema != "" {
		connConfig.RuntimeParams["search_path"] = cfg.DefaultSchema
	}

	// Parse and apply connection options if specified
	if cfg.ConnOptions != "" {
		connOpts, err := parseConnOptions(cfg.ConnOptions)
		if err != nil {
			return nil, fmt.Errorf("failed to parse connection options: %w", err)
		}

		// Apply each connection option to the appropriate config field
		if err := applyConnOptions(connConfig, connOpts); err != nil {
			return nil, fmt.Errorf("failed to apply connection options: %w", err)
		}
	}

	return connConfig, nil
}

// parseConnOptions decodes a base64-encoded JSON string into a map of connection options.
// This matches the Python behavior in authentik/lib/config.py:get_dict_from_b64_json
func parseConnOptions(encoded string) (map[string]string, error) {
	// Base64 decode
	decoded, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil {
		return nil, fmt.Errorf("invalid base64 encoding: %w", err)
	}

	// Parse JSON
	var opts map[string]interface{}
	if err := json.Unmarshal(decoded, &opts); err != nil {
		return nil, fmt.Errorf("invalid JSON: %w", err)
	}

	// Convert all values to strings
	result := make(map[string]string)
	for k, v := range opts {
		switch val := v.(type) {
		case string:
			result[k] = val
		case float64:
			// JSON numbers are float64
			if val == float64(int(val)) {
				result[k] = strconv.Itoa(int(val))
			} else {
				result[k] = strconv.FormatFloat(val, 'f', -1, 64)
			}
		case bool:
			result[k] = strconv.FormatBool(val)
		default:
			result[k] = fmt.Sprintf("%v", v)
		}
	}

	return result, nil
}

// applyConnOptions applies parsed connection options to the pgx.ConnConfig.
func applyConnOptions(connConfig *pgx.ConnConfig, opts map[string]string) error {
	for key, value := range opts {
		// connect_timeout needs special handling as it's a connection-level timeout
		if key == "connect_timeout" {
			timeout, err := strconv.Atoi(value)
			if err != nil {
				return fmt.Errorf("invalid connect_timeout value: %w", err)
			}
			connConfig.ConnectTimeout = time.Duration(timeout) * time.Second
			continue
		}
		// All other options go to RuntimeParams
		connConfig.RuntimeParams[key] = value
	}
	return nil
}

// BuildDSN constructs a PostgreSQL connection string from a ConnConfig.
func BuildDSN(cfg config.PostgreSQLConfig) (string, error) {
	connConfig, err := BuildConnConfig(cfg)
	if err != nil {
		return "", err
	}

	// Register the config and get a connection string
	// (This approach lets pgx handle all the escaping internally which is quite convenient for say spaces in the password)
	return stdlib.RegisterConnConfig(connConfig), nil
}

// SetupGORMWithRefreshablePool creates a GORM DB with a refreshable connection pool.
// This is the standardized way to create database connections for both production and tests.
//
// The RefreshableConnPool wraps database/sql and automatically detects PostgreSQL
// authentication errors (SQLSTATE 28xxx), refreshes credentials from config sources
// (file://, env://, or plain environment variables), and reconnects without downtime.
//
// Parameters:
//   - cfg: PostgreSQL configuration (host, port, user, password, etc.)
//   - gormConfig: GORM configuration (logger, naming strategy, etc.)
//   - maxIdleConns: Maximum number of idle connections in the pool
//   - maxOpenConns: Maximum number of open connections to the database
//   - connMaxLifetime: Maximum lifetime of a connection
//
// Returns:
//   - *gorm.DB: GORM database instance for ORM operations
//   - *RefreshableConnPool: Connection pool reference (caller must Close when done)
//   - error: Any error encountered during setup
func SetupGORMWithRefreshablePool(cfg config.PostgreSQLConfig, gormConfig *gorm.Config, maxIdleConns, maxOpenConns int, connMaxLifetime time.Duration) (*gorm.DB, *RefreshableConnPool, error) {
	// Build connection string
	dsn, err := BuildDSN(cfg)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to build DSN: %w", err)
	}

	// Create refreshable connection pool
	pool, err := NewRefreshableConnPool(dsn, gormConfig, maxIdleConns, maxOpenConns, connMaxLifetime)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Create GORM DB using the refreshable connection pool
	db, err := pool.NewGORMDB()
	if err != nil {
		_ = pool.Close()
		return nil, nil, fmt.Errorf("failed to connect to PostgreSQL: %w", err)
	}

	// Test the connection with a simple query
	// This will trigger the connection pool's tryWithRefresh logic if there's an auth error
	ctx := context.Background()
	var result int
	err = db.WithContext(ctx).Raw("SELECT 1").Scan(&result).Error
	if err != nil {
		_ = pool.Close()
		return nil, nil, fmt.Errorf("failed to connect to PostgreSQL: %w", err)
	}

	return db, pool, nil
}

// NewPostgresStore returns a new PostgresStore
func NewPostgresStore(log *log.Entry) (*PostgresStore, error) {
	cfg := config.Get().PostgreSQL

	// Configure GORM
	gormConfig := &gorm.Config{
		Logger: NewLogger(log),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	}

	// Determine connection pool settings
	maxIdleConns := 10
	maxOpenConns := 100
	var connMaxLifetime time.Duration
	if cfg.ConnMaxAge > 0 {
		connMaxLifetime = time.Duration(cfg.ConnMaxAge) * time.Second
	} else {
		connMaxLifetime = time.Hour // Default 1 hour
	}

	// Use standardized setup
	db, pool, err := SetupGORMWithRefreshablePool(cfg, gormConfig, maxIdleConns, maxOpenConns, connMaxLifetime)
	if err != nil {
		return nil, fmt.Errorf("failed to setup database: %w", err)
	}

	ps := &PostgresStore{
		db:   db,
		pool: pool,
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

	err = s.load(r.Context(), session)
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
		if err := s.delete(r.Context(), session); err != nil {
			return fmt.Errorf("failed to delete session: %w", err)
		}
		http.SetCookie(w, sessions.NewCookie(session.Name(), "", session.Options))
		return nil
	}

	if session.ID == "" {
		// Generate new session ID
		session.ID = s.keyPrefix + generateSessionID()
	}

	if err := s.save(r.Context(), session); err != nil {
		return fmt.Errorf("failed to save session: %w", err)
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
	if s.pool != nil {
		return s.pool.Close()
	}
	return nil
}

// save writes session to PostgreSQL
func (s *PostgresStore) save(ctx context.Context, session *sessions.Session) error {
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
		Expiring:    true,
	}

	// Add expiration timestamp to session data
	if session.Options != nil && session.Options.MaxAge > 0 {
		expiresAt := time.Now().UTC().Add(time.Duration(session.Options.MaxAge) * time.Second)
		proxySession.Expires = expiresAt
	}

	return s.db.WithContext(ctx).Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "session_key"}},
		DoUpdates: clause.AssignmentColumns([]string{"user_id", "session_data", "expires"}),
	}).Create(&proxySession).Error
}

// load reads session from PostgreSQL
func (s *PostgresStore) load(ctx context.Context, session *sessions.Session) error {
	var proxySession ProxySession
	err := s.db.WithContext(ctx).Where("session_key = ?", session.ID).First(&proxySession).Error

	if err != nil {
		return fmt.Errorf("failed to load session: %w", err)
	}

	// Check if session is expired
	if time.Now().UTC().After(proxySession.Expires) {
		// Session is expired, delete it and return not found error
		s.db.WithContext(ctx).Delete(&ProxySession{}, "session_key = ?", session.ID)
		return gorm.ErrRecordNotFound
	}

	// Deserialize session data from JSON
	if proxySession.SessionData != "" {
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
func (s *PostgresStore) delete(ctx context.Context, session *sessions.Session) error {
	return s.db.WithContext(ctx).Delete(&ProxySession{}, "session_key = ?", session.ID).Error
}

// CleanupExpired removes expired sessions by checking MaxAge in session_data
func (s *PostgresStore) CleanupExpired(ctx context.Context) error {
	result := s.db.WithContext(ctx).Where(`"expires" < ?`, time.Now().UTC()).Delete(&ProxySession{})
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
	err := s.db.WithContext(ctx).Where(fmt.Sprintf("session_data::jsonb ? '%s'", constants.SessionClaims)).Find(&sessions).Error
	if err != nil {
		return fmt.Errorf("failed to fetch sessions: %w", err)
	}

	var sessionKeysToDelete []string

	for _, session := range sessions {
		if session.SessionData == "" {
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
		err = s.db.WithContext(ctx).Delete(&ProxySession{}, "session_key IN ?", sessionKeysToDelete).Error
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

// NewTestStore creates a PostgresStore for testing with the given database and pool.
// The pool reference is required to properly close connections in test cleanup.
func NewTestStore(db *gorm.DB, pool *RefreshableConnPool) *PostgresStore {
	return &PostgresStore{
		db:   db,
		pool: pool,
		options: sessions.Options{
			Path:   "/",
			MaxAge: 3600,
		},
		keyPrefix: "test_session_",
		log:       log.WithField("logger", "test"),
	}
}
