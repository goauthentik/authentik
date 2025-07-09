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

// is this used
const SQLiteKeyPrefix = "authentik_proxy_session_"
const PostgresKeyPrefix = "authentik_proxy_session_"
const PostgresSchema = "public"
const DefaultSQLiteDBName = "authentik_proxy_outpost.sqlite"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) (sessions.Store, error) {
	maxAge := 0
	if p.AccessTokenValidity.IsSet() {
		t := p.AccessTokenValidity.Get()
		// Add one to the validity to ensure we don't have a session with indefinite length
		maxAge = int(*t) + 1
	}

	if a.isEmbedded {
		// Use Postgres for embedded outposts
		pgConfig := config.Get().Storage.PostgreSQL

		port := pgConfig.Port
		dbName := pgConfig.Name // todo why did I do this
		pgConnStr := fmt.Sprintf("host=%s port=%d dbname=%s user=%s password=%s",
			pgConfig.Host,
			port,
			dbName,
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

		// might fail if missing critical (so not ssl) todo mabye
		if pgConfig.Host == "" || pgConfig.User == "" {
			return nil, fmt.Errorf("PostgreSQL connection not properly configured for embedded outpost")
		}

		// Log connection details (without password)
		a.log.WithFields(log.Fields{
			"host":     pgConfig.Host,
			"port":     port,
			"dbname":   dbName,
			"user":     pgConfig.User,
			"schema":   PostgresSchema,
			"sslmode":  pgConfig.SSLMode,
			"has_cert": pgConfig.SSLCert != "",
		}).Debug("Connecting to PostgreSQL")

		providerID := strconv.Itoa(int(p.GetPk()))
		store, err := pgstore.NewPGStore(pgConnStr, PostgresSchema, providerID)
		if err != nil {
			if isPGTableMissingError(err) {
				a.log.WithError(err).Error("PostgreSQL session table is missing. Please run Django migrations.")
				return nil, fmt.Errorf("PostgreSQL session table is missing: %w", err)
			}
			return nil, fmt.Errorf("failed to create PostgreSQL store: %w", err)
		}
		store.KeyPrefix(PostgresKeyPrefix)
		store.Options(sessions.Options{
			HttpOnly: true,
			Secure:   strings.ToLower(externalHost.Scheme) == "https",
			Domain:   *p.CookieDomain,
			SameSite: http.SameSiteLaxMode,
			MaxAge:   maxAge,
			Path:     "/",
		})
		a.log.WithField("schema", PostgresSchema).Info("Using PostgreSQL session backend")
		return store, nil
	}

	// Use SQLite for regular outposts
	dbPath := config.Get().SQLite.Path
	if dbPath == "" {
		tempDir, err := os.MkdirTemp("", "authentik-proxy-*")
		if err != nil {
			return nil, fmt.Errorf("failed to create temp directory for SQLite database: %w", err)
		}
		dbPath = filepath.Join(tempDir, DefaultSQLiteDBName)
		a.log.WithField("path", dbPath).Info("Created SQLite database in temporary directory")
	} else {
		a.log.WithField("path", dbPath).Info("Using configured SQLite database path")
	}

	providerID := strconv.Itoa(int(p.GetPk()))
	store, err := sqlitestore.NewSQLiteStore(dbPath, providerID)
	if err != nil {
		return nil, fmt.Errorf("failed to create SQLite store: %w", err)
	}
	store.KeyPrefix(SQLiteKeyPrefix)
	store.Options(sessions.Options{
		HttpOnly: true,
		Secure:   strings.ToLower(externalHost.Scheme) == "https",
		Domain:   *p.CookieDomain,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   maxAge,
		Path:     "/",
	})
	// Prune expired sessions on startup
	err = pruneExpiredSQLiteSessions(store)
	if err != nil {
		a.log.WithError(err).Warning("Failed to prune expired SQLite sessions on startup")
	}

	a.log.WithField("path", dbPath).Info("Using SQLite session backend")
	return store, nil
}

// pruneExpiredSQLiteSessions deletes expired sessions from the SQLite DB
// This is only run once on startup for initial cleanup (mabye not needed)
func pruneExpiredSQLiteSessions(store *sqlitestore.SQLiteStore) error {
	rowsAffected, err := store.CleanupExpired(context.Background())
	if err != nil {
		return err
	}
	if rowsAffected > 0 {
		log.WithField("rows_affected", rowsAffected).Debug("Pruned expired SQLite sessions on startup")
	}
	return nil
}

func (a *Application) SessionName() string {
	return a.sessionName
}

func (a *Application) Logout(ctx context.Context, filter func(c Claims) bool) error {
	if ss, ok := a.sessions.(*sqlitestore.SQLiteStore); ok {
		return a.logoutFromStore(ctx, ss, filter)
	} else if ps, ok := a.sessions.(*pgstore.PGStore); ok {
		return a.logoutFromStore(ctx, ps, filter)
	}
	return fmt.Errorf("unknown session store type")
}

// logoutFromStore handles logout from any store that implements the required methods
type sessionStoreWithDelete interface {
	GetAllSessions(ctx context.Context) ([]*sessions.Session, error)
	Delete(ctx context.Context, session *sessions.Session) error
}

func (a *Application) logoutFromStore(ctx context.Context, store sessionStoreWithDelete, filter func(c Claims) bool) error {
	sessions, err := store.GetAllSessions(ctx)
	if err != nil {
		return fmt.Errorf("failed to get sessions: %w", err)
	}

	for _, session := range sessions {
		rc, ok := session.Values[constants.SessionClaims]
		if !ok || rc == nil {
			continue
		}
		claims := rc.(Claims)
		if filter(claims) {
			a.log.WithField("session_id", session.ID).Trace("deleting session")
			if err := store.Delete(ctx, session); err != nil {
				a.log.WithError(err).Warning("failed to delete session")
			}
		}
	}
	return nil
}

// Helper to check for missing table error
func isPGTableMissingError(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(err.Error(), "does not exist") && strings.Contains(err.Error(), "relation")
}
