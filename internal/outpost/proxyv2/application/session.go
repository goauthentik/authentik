package application

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/gorilla/sessions"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/sqlitestore"
)

const SQLiteKeyPrefix = "authentik_proxy_session_"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) (sessions.Store, error) {
	maxAge := 0
	if p.AccessTokenValidity.IsSet() {
		t := p.AccessTokenValidity.Get()
		// Add one to the validity to ensure we don't have a session with indefinite length
		maxAge = int(*t) + 1
	}

	// Ensure data directory exists
	dataDir := filepath.Dir(config.Get().SQLite.Path)
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create data directory: %w", err)
	}

	// Default cleanup interval is 1 hour if not specified
	cleanupInterval := time.Duration(config.Get().SQLite.CleanupInterval) * time.Second
	if cleanupInterval == 0 {
		cleanupInterval = time.Hour
	}

	// Create SQLite store
	store, err := sqlitestore.NewSQLiteStore(config.Get().SQLite.Path, cleanupInterval)
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

	a.log.WithField("path", config.Get().SQLite.Path).Trace("using SQLite session backend")
	return store, nil
}

func (a *Application) SessionName() string {
	return a.sessionName
}

func (a *Application) Logout(ctx context.Context, filter func(c Claims) bool) error {
	if ss, ok := a.sessions.(*sqlitestore.SQLiteStore); ok {
		sessions, err := ss.GetAllSessions(ctx)
		if err != nil {
			return err
		}

		for _, session := range sessions {
			rc, ok := session.Values[constants.SessionClaims]
			if !ok || rc == nil {
				continue
			}
			claims := rc.(Claims)
			if filter(claims) {
				a.log.WithField("session_id", session.ID).Trace("deleting session")
				err := ss.Delete(ctx, session)
				if err != nil {
					a.log.WithError(err).Warning("failed to delete session")
					continue
				}
			}
		}
	}
	return nil
}
