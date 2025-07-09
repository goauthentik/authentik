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

	"goauthentik.io/api/v3"
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

	// For embedded outposts, use PostgreSQL directly
	if a.isEmbedded {
		return a.getPostgresStore(p, externalHost, maxAge)
	}

	// For non-embedded outposts, use SQLite in a temporary directory
	return a.getSQLiteStore(p, externalHost, maxAge)
}

// getPostgresStore initializes and returns a PostgreSQL session store
func (a *Application) getPostgresStore(p api.ProxyOutpostConfig, externalHost *url.URL, maxAge int) (sessions.Store, error) {
	// todo undo this deleted bit on how to conn to pg
	pgConnStr := "abc"

	// Get provider ID as string
	providerID := strconv.Itoa(int(p.GetPk()))

	// Create PostgreSQL store
	store, err := pgstore.NewPGStore(pgConnStr, PostgresSchema, providerID)
	if err != nil {
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

// getSQLiteStore initializes and returns a SQLite session store
func (a *Application) getSQLiteStore(p api.ProxyOutpostConfig, externalHost *url.URL, maxAge int) (sessions.Store, error) {
	// Always use a temporary directory for SQLite database
	tempDir, err := os.MkdirTemp("", "authentik-proxy-*")
	if err != nil {
		return nil, fmt.Errorf("failed to create temp directory for SQLite database: %w", err)
	}
	dbPath := filepath.Join(tempDir, DefaultSQLiteDBName)
	a.log.WithField("path", dbPath).Info("Created SQLite database in temporary directory")

	// Get provider ID as string
	providerID := strconv.Itoa(int(p.GetPk()))

	// Create SQLite store
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

	a.log.WithField("path", dbPath).Info("Using SQLite session backend")
	return store, nil
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
