package application

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/api/v3"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"goauthentik.io/internal/outpost/proxyv2/pgstore"
	"goauthentik.io/internal/outpost/proxyv2/sqlitestore"
)

const SQLiteKeyPrefix = "authentik_proxy_"
const PostgresKeyPrefix = "authentik_proxy_"
const PostgresSchema = "public"

func (a *Application) getStore(p api.ProxyOutpostConfig, externalHost *url.URL) (sessions.Store, error) {
	a.log.WithField("is_embedded", a.isEmbedded).Debug("Initializing session store")

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
	providerID := strconv.Itoa(int(p.GetPk()))
	a.log.WithField("provider_id", providerID).Debug("Using provider ID for PostgreSQL store")

	store, err := pgstore.CreateStoreFromConfig(PostgresSchema, providerID, &sessionOptions, a.log)
	if err != nil {
		if pgstore.IsTableMissingError(err) {
			a.log.WithError(err).Error("PostgreSQL session table is missing. Please run Django migrations.")
			return nil, fmt.Errorf("PostgreSQL session table is missing: %w", err)
		}
		a.log.WithError(err).Error("Failed to create PostgreSQL store")
		return nil, fmt.Errorf("failed to create PostgreSQL store: %w", err)
	}

	return store, nil
}

// createSQLiteStore creates a SQLite session store
func (a *Application) createSQLiteStore(p api.ProxyOutpostConfig, sessionOptions sessions.Options) (sessions.Store, error) {
	providerID := strconv.Itoa(int(p.GetPk()))
	a.log.WithField("provider_id", providerID).Debug("Using provider ID for SQLite store")

	a.log.Debug("Creating SQLite session store for standalone outpost")

	store, err := sqlitestore.CreateStoreFromConfig(providerID, &sessionOptions, a.log)
	if err != nil {
		a.log.WithError(err).Error("Failed to create SQLite store")
		return nil, fmt.Errorf("failed to create SQLite store: %w", err)
	}

	return store, nil
}

// SessionName returns the name of the session
func (a *Application) SessionName() string {
	a.log.WithField("session_name", a.sessionName).Debug("Getting session name")
	return a.sessionName
}

// Logout logs out from the session store
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

// logoutFromStore logs out from the session store
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
		a.log.WithField("session_id", session.ID).WithField("claims_sid", claims.Sid).WithField("sub", claims.Sub).WithField("username", claims.PreferredUsername).Debug("Checking session for logout")

		if filter(claims) {
			a.log.WithFields(log.Fields{
				"session_id": session.ID,
				"sub":        claims.Sub,
				"username":   claims.PreferredUsername,
				"claims_sid": claims.Sid,
			}).Info("Deleting session - filter matched")
			if err := store.Delete(ctx, session); err != nil {
				a.log.WithError(err).WithField("session_id", session.ID).Warning("Failed to delete session")
			} else {
				a.log.WithField("session_id", session.ID).Info("Successfully deleted session")
				deletedCount++
			}
		} else {
			a.log.WithField("session_id", session.ID).WithField("claims_sid", claims.Sid).Debug("Session does not match filter criteria, keeping")
		}
	}

	a.log.WithField("deleted_count", deletedCount).Info("Completed logout process")
	return nil
}
