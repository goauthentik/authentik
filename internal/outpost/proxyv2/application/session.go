package application

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/pgstore"
	"goauthentik.io/internal/outpost/proxyv2/sqlitestore"
)

const SQLiteKeyPrefix = "authentik_proxy_session_"
const PostgresKeyPrefix = "authentik_proxy_session_"
const PostgresSchema = "public"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) (sessions.Store, error) {
	a.log.Debug("Initializing session store")

	maxAge := 0
	if p.AccessTokenValidity.IsSet() {
		t := p.AccessTokenValidity.Get()
		// Add one to the validity to ensure we don't have a session with indefinite length
		maxAge = int(*t) + 1
		a.log.WithField("max_age", maxAge).Debug("Setting session max age from access token validity")
	} else {
		a.log.Debug("No access token validity set, using default max age")
	}

	sessionOptions := sessions.Options{
		HttpOnly: true,
		Secure:   strings.ToLower(externalHost.Scheme) == "https",
		Domain:   *p.CookieDomain,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   maxAge,
		Path:     "/",
	}

	if a.isEmbedded {
		a.log.Debug("Using PostgreSQL for embedded outpost")
		return a.createPostgreSQLStore(p, sessionOptions)
	}

	a.log.Debug("Using SQLite for non-embedded outpost")
	return a.createSQLiteStore(p, sessionOptions)
}

func (a *Application) createPostgreSQLStore(p api.ProxyOutpostConfig, sessionOptions sessions.Options) (sessions.Store, error) {
	// Use Postgres for embedded outposts
	pgConfig := config.Get().Storage.PostgreSQL

	pgConnStr := fmt.Sprintf("host=%s port=%d dbname=%s user=%s password=%s",
		pgConfig.Host,
		pgConfig.Port,
		pgConfig.Name,
		pgConfig.User,
		pgConfig.Password,
	)

	if pgConfig.SSLMode != "" {
		pgConnStr += fmt.Sprintf(" sslmode=%s", pgConfig.SSLMode)
	}
	if pgConfig.SSLRootCert != "" {
		pgConnStr += fmt.Sprintf(" sslrootcert=%s", pgConfig.SSLRootCert)
	}
	if pgConfig.SSLCert != "" {
		pgConnStr += fmt.Sprintf(" sslcert=%s", pgConfig.SSLCert)
	}
	if pgConfig.SSLKey != "" {
		pgConnStr += fmt.Sprintf(" sslkey=%s", pgConfig.SSLKey)
	}

	if pgConfig.Host == "" || pgConfig.User == "" {
		a.log.Error("PostgreSQL connection not properly configured for embedded outpost")
		return nil, fmt.Errorf("PostgreSQL connection not properly configured for embedded outpost")
	}

	// Log connection details (without password)
	a.log.WithFields(log.Fields{
		"host":     pgConfig.Host,
		"port":     pgConfig.Port,
		"dbname":   pgConfig.Name,
		"user":     pgConfig.User,
		"schema":   PostgresSchema,
		"sslmode":  pgConfig.SSLMode,
		"has_cert": pgConfig.SSLCert != "",
	}).Debug("Connecting to PostgreSQL")

	providerID := strconv.Itoa(int(p.GetPk()))
	a.log.WithField("provider_id", providerID).Debug("Using provider ID for PostgreSQL store")

	store, err := pgstore.NewPGStore(pgConnStr, PostgresSchema, providerID, &sessionOptions)
	if err != nil {
		if isPGTableMissingError(err) {
			a.log.WithError(err).Error("PostgreSQL session table is missing. Please run Django migrations.")
			return nil, fmt.Errorf("PostgreSQL session table is missing: %w", err)
		}
		a.log.WithError(err).Error("Failed to create PostgreSQL store")
		return nil, fmt.Errorf("failed to create PostgreSQL store: %w", err)
	}

	a.log.WithField("schema", PostgresSchema).Info("Using PostgreSQL session backend")
	return store, nil
}

func (a *Application) createSQLiteStore(p api.ProxyOutpostConfig, sessionOptions sessions.Options) (sessions.Store, error) {
	// Get provider ID
	providerID := strconv.Itoa(int(p.GetPk()))
	a.log.WithField("provider_id", providerID).Debug("Using provider ID for SQLite store")

	// Determine database directory
	var dbDir string
	if _, err := os.Stat("/dev/shm"); err == nil {
		dbDir = filepath.Join("/dev/shm", "authentik-sessions")
	} else {
		dbDir = filepath.Join(os.TempDir(), "authentik-sessions")
	}

	// Create the directory if it doesn't exist
	if err := os.MkdirAll(dbDir, 0755); err != nil {
		a.log.WithError(err).Error("Failed to create directory for SQLite database")
		return nil, fmt.Errorf("failed to create directory for SQLite database: %w", err)
	}

	// Use a single database file for all providers
	dbPath := filepath.Join(dbDir, "sessions.sqlite")
	a.log.WithFields(log.Fields{
		"db_dir":      dbDir,
		"db_path":     dbPath,
		"provider_id": providerID,
	}).Info("Using shared SQLite database for session storage")

	store, err := sqlitestore.NewSQLiteStore(dbPath, providerID, &sessionOptions)
	if err != nil {
		a.log.WithError(err).WithField("db_path", dbPath).Error("Failed to create SQLite store")
		return nil, fmt.Errorf("failed to create SQLite store: %w", err)
	}

	// Start periodic cleanup of expired sessions
	cleanupInterval := config.Get().SQLite.CleanupInterval
	a.log.WithField("interval_seconds", cleanupInterval).Debug("Starting periodic cleanup of expired sessions")
	store.StartPeriodicCleanup(context.Background(), cleanupInterval)

	a.log.WithField("path", dbPath).Info("Using SQLite session backend")
	return store, nil
}

func (a *Application) SessionName() string {
	a.log.WithField("session_name", a.sessionName).Debug("Getting session name")
	return a.sessionName
}

func (a *Application) Logout(ctx context.Context, filter func(c Claims) bool) error {
	a.log.Debug("Logging out user sessions")

	// Both stores now implement the same interface
	if store, ok := a.sessions.(sessionStoreWithDelete); ok {
		a.log.Debug("Using session store for logout")
		return a.logoutFromStore(ctx, store, filter)
	}

	a.log.Error("Session store does not support required operations")
	return fmt.Errorf("session store does not support required operations")
}

// sessionStoreWithDelete defines the interface needed for logout functionality
type sessionStoreWithDelete interface {
	GetAllSessions(ctx context.Context) ([]*sessions.Session, error)
	Delete(ctx context.Context, session *sessions.Session) error
}

func (a *Application) logoutFromStore(ctx context.Context, store sessionStoreWithDelete, filter func(c Claims) bool) error {
	a.log.Debug("Getting all sessions for logout")
	sessions, err := store.GetAllSessions(ctx)
	if err != nil {
		a.log.WithError(err).Error("Failed to get sessions for logout")
		return fmt.Errorf("failed to get sessions: %w", err)
	}

	a.log.WithField("session_count", len(sessions)).Debug("Found sessions for potential logout")
	deletedCount := 0

	for _, session := range sessions {
		rc, ok := session.Values[constants.SessionClaims]
		if !ok || rc == nil {
			a.log.WithField("session_id", session.ID).Debug("Session has no claims, skipping")
			continue
		}
		claims := rc.(Claims)
		if filter(claims) {
			a.log.WithFields(log.Fields{
				"session_id": session.ID,
				"sub":        claims.Sub,
				"username":   claims.PreferredUsername,
			}).Debug("Deleting session")
			if err := store.Delete(ctx, session); err != nil {
				a.log.WithError(err).WithField("session_id", session.ID).Warning("Failed to delete session")
			} else {
				deletedCount++
			}
		} else {
			a.log.WithField("session_id", session.ID).Debug("Session does not match filter criteria, keeping")
		}
	}

	a.log.WithField("deleted_count", deletedCount).Debug("Completed logout process")
	return nil
}

// Helper to check for missing table error
func isPGTableMissingError(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(err.Error(), "does not exist") && strings.Contains(err.Error(), "relation")
}
