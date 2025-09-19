package postgresstore

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	"github.com/jackc/pgx/v5"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
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
}

// ProxySession represents the session data structure in PostgreSQL
type ProxySession struct {
	SessionKey   string     `gorm:"primaryKey;size:255;column:session_key"`
	UserID       *uuid.UUID `gorm:"index;column:user_id"`
	UserEmail    string     `gorm:"size:254;column:user_email"`
	UserUsername string     `gorm:"size:150;column:user_username"`
	AccessToken  string     `gorm:"type:text;column:access_token"`
	RefreshToken string     `gorm:"type:text;column:refresh_token"`
	IDToken      string     `gorm:"type:text;column:id_token"`
	CreatedAt    time.Time  `gorm:"autoCreateTime;index;column:created_at"`
	LastAccessed time.Time  `gorm:"autoUpdateTime;index;column:last_accessed"`
	ExpiresAt    time.Time  `gorm:"index;column:expires_at"`
	ExtraClaims  string     `gorm:"type:jsonb;column:extra_claims;default:'{}'"`
	SessionData  string     `gorm:"type:jsonb;column:session_data;default:'{}'"`
}

// TableName specifies the table name for GORM
func (ProxySession) TableName() string {
	return "authentik_outposts_proxy_session"
}

// buildDSN constructs a PostgreSQL connection string using pgx natively
func buildDSN(cfg config.PostgreSQLConfig) (string, error) {
	// Build DSN string with all parameters and let pgx parse it properly
	dsnParts := []string{
		"host=" + cfg.Host,
		fmt.Sprintf("port=%d", cfg.Port),
		"user=" + cfg.User,
		"password=" + cfg.Password,
		"dbname=" + cfg.Name,
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

	// Add schema if specified
	if cfg.DefaultSchema != "" {
		dsnParts = append(dsnParts, "search_path="+cfg.DefaultSchema)
	}

	// Add connection options if specified
	if cfg.ConnOptions != "" {
		dsnParts = append(dsnParts, cfg.ConnOptions)
	}

	// Join parts with spaces
	dsnString := strings.Join(dsnParts, " ")

	// Let pgx parse and validate the entire DSN
	pgxConfig, err := pgx.ParseConfig(dsnString)
	if err != nil {
		return "", fmt.Errorf("failed to parse DSN: %w", err)
	}

	// Return the DSN
	return pgxConfig.ConnString(), nil
}

// NewPostgresStore returns a new PostgresStore
func NewPostgresStore() (*PostgresStore, error) {
	cfg := config.Get().PostgreSQL

	// Build connection string
	dsn, err := buildDSN(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to build DSN: %w", err)
	}

	// Configure GORM
	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
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
			MaxAge: 86400 * 30, // 30 days default todo(dominic): validate if it was that before
		},
		keyPrefix: "authentik_proxy_session_",
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

	// Extract user information from claims if they exist for the db columns
	var userID *uuid.UUID
	userEmail := ""
	userUsername := ""
	accessToken := ""
	refreshToken := ""
	idToken := ""
	extraClaimsJSON := []byte("{}")

	if claims, hasClaims := session.Values[constants.SessionClaims]; hasClaims {
		if claimsMap, ok := claims.(map[string]interface{}); ok {
			if sub, exists := claimsMap["sub"]; exists {
				if subStr, ok := sub.(string); ok {
					if parsedUUID, err := uuid.Parse(subStr); err == nil {
						userID = &parsedUUID
					}
				}
			}

			// todo(dominic): Fix basically the same logic being repeated
			if email, exists := claimsMap["email"]; exists {
				if emailStr, ok := email.(string); ok {
					userEmail = emailStr
				}
			}

			if username, exists := claimsMap["preferred_username"]; exists {
				if usernameStr, ok := username.(string); ok {
					userUsername = usernameStr
				}
			}

			if token, exists := claimsMap["access_token"]; exists {
				if tokenStr, ok := token.(string); ok {
					accessToken = tokenStr
				}
			}

			if token, exists := claimsMap["refresh_token"]; exists {
				if tokenStr, ok := token.(string); ok {
					refreshToken = tokenStr
				}
			}

			if token, exists := claimsMap["id_token"]; exists {
				if tokenStr, ok := token.(string); ok {
					idToken = tokenStr
				}
			}

			// Serialize extra claims (everything not extracted above)
			extraClaims := make(map[string]interface{})
			skipKeys := map[string]bool{ // todo(dominic): eh this looks a little cheap
				"sub": true, "email": true, "preferred_username": true,
				"access_token": true, "refresh_token": true, "id_token": true,
			}
			for key, value := range claimsMap {
				if !skipKeys[key] {
					extraClaims[key] = value
				}
			}
			extraClaimsJSON, _ = json.Marshal(extraClaims)
		}
	}

	// Calculate expiration time
	expiresAt := time.Now().Add(time.Duration(session.Options.MaxAge) * time.Second)

	proxySession := ProxySession{
		SessionKey:   session.ID,
		UserID:       userID,
		UserEmail:    userEmail,
		UserUsername: userUsername,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		IDToken:      idToken,
		ExpiresAt:    expiresAt,
		ExtraClaims:  string(extraClaimsJSON),
		SessionData:  string(sessionData),
	}

	return s.db.Save(&proxySession).Error
}

// load reads session from PostgreSQL
func (s *PostgresStore) load(session *sessions.Session) error {
	var proxySession ProxySession
	err := s.db.Where("session_key = ? AND expires_at > ?", session.ID, time.Now()).
		First(&proxySession).Error

	if err != nil {
		return err
	}

	// todo(dominic): clean up all of this

	// Deserialize complete session data first (preferred method)
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
	} else {
		// Fallback if session_data is empty
		if proxySession.UserID != nil || proxySession.UserEmail != "" {
			claims := make(map[string]interface{})

			if proxySession.UserID != nil {
				claims["sub"] = proxySession.UserID.String()
			}
			if proxySession.UserEmail != "" {
				claims["email"] = proxySession.UserEmail
			}
			if proxySession.UserUsername != "" {
				claims["preferred_username"] = proxySession.UserUsername
			}
			if proxySession.AccessToken != "" {
				claims["access_token"] = proxySession.AccessToken
			}
			if proxySession.RefreshToken != "" {
				claims["refresh_token"] = proxySession.RefreshToken
			}
			if proxySession.IDToken != "" {
				claims["id_token"] = proxySession.IDToken
			}

			// Deserialize extra claims
			if proxySession.ExtraClaims != "" && proxySession.ExtraClaims != "{}" {
				var extraClaims map[string]interface{}
				if err := json.Unmarshal([]byte(proxySession.ExtraClaims), &extraClaims); err == nil {
					for key, value := range extraClaims {
						claims[key] = value
					}
				}
			}

			session.Values[constants.SessionClaims] = claims
		}
	}

	// Update last accessed time
	s.db.Model(&proxySession).Update("last_accessed", time.Now())

	return nil
}

// delete removes session from PostgreSQL
func (s *PostgresStore) delete(session *sessions.Session) error {
	return s.db.Delete(&ProxySession{}, "session_key = ?", session.ID).Error
}

// CleanupExpired removes expired sessions
func (s *PostgresStore) CleanupExpired() error {
	return s.db.Delete(&ProxySession{}, "expires_at <= ?", time.Now()).Error
}

// LogoutSessions removes sessions that match the given filter criteria
// The filter function should return true for sessions that should be deleted
func (s *PostgresStore) LogoutSessions(ctx context.Context, filter func(c types.Claims) bool) error {
	// First, retrieve all non-expired sessions
	var sessions []ProxySession
	err := s.db.Where("expires_at > ?", time.Now()).Find(&sessions).Error
	if err != nil {
		return fmt.Errorf("failed to fetch sessions: %w", err)
	}

	var sessionKeysToDelete []string

	for _, session := range sessions {
		// Reconstruct claims from database columns
		claims := types.Claims{}

		if session.UserID != nil {
			claims.Sub = session.UserID.String()
		}
		if session.UserEmail != "" {
			claims.Email = session.UserEmail
		}
		if session.UserUsername != "" {
			claims.PreferredUsername = session.UserUsername
		}

		// Parse extra claims to extract additional fields
		if session.ExtraClaims != "" && session.ExtraClaims != "{}" {
			var extraClaims map[string]interface{}
			if err := json.Unmarshal([]byte(session.ExtraClaims), &extraClaims); err == nil {
				// Extract known fields from extra claims
				if exp, ok := extraClaims["exp"].(float64); ok {
					claims.Exp = int(exp)
				}
				if verified, ok := extraClaims["email_verified"].(bool); ok {
					claims.Verified = verified
				}
				if name, ok := extraClaims["name"].(string); ok {
					claims.Name = name
				}
				if groups, ok := extraClaims["groups"].([]interface{}); ok {
					for _, group := range groups {
						if groupStr, ok := group.(string); ok {
							claims.Groups = append(claims.Groups, groupStr)
						}
					}
				}
				if entitlements, ok := extraClaims["entitlements"].([]interface{}); ok {
					for _, entitlement := range entitlements {
						if entitlementStr, ok := entitlement.(string); ok {
							claims.Entitlements = append(claims.Entitlements, entitlementStr)
						}
					}
				}
				if sid, ok := extraClaims["sid"].(string); ok {
					claims.Sid = sid
				}
			}
		}

		// Apply filter function
		if filter(claims) {
			sessionKeysToDelete = append(sessionKeysToDelete, session.SessionKey)
		}
	}

	// Delete sessions that matched the filter
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
