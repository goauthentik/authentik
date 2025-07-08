package sessionstore

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"
	"go.uber.org/multierr"
	"goauthentik.io/internal/outpost/proxyv2/constants"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

const (
	// Operation timeouts
	DefaultOperationTimeout = 30 * time.Second
	DefaultRetryAttempts    = 3
	DefaultRetryDelay       = 100 * time.Millisecond
)

// RetryConfig holds configuration for retry operations
type RetryConfig struct {
	MaxAttempts int
	Delay       time.Duration
	Backoff     float64 // Multiplier for exponential backoff
}

// DefaultRetryConfig returns sensible defaults for retry operations
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxAttempts: DefaultRetryAttempts,
		Delay:       DefaultRetryDelay,
		Backoff:     2.0,
	}
}

// GormStore is an interface that a GORM-based session store must implement
type GormStore interface {
	SessionStore
	GetDB() *gorm.DB
	NowValue() string
}

// executeWithRetry executes a database operation with retry logic
func executeWithRetry(ctx context.Context, operation func() error, config RetryConfig) error {
	var lastErr error
	delay := config.Delay

	for attempt := 1; attempt <= config.MaxAttempts; attempt++ {
		if attempt > 1 {
			// Check if context is cancelled before retrying
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(delay):
				// Continue with retry
			}
		}

		if err := operation(); err != nil {
			lastErr = err

			// Don't retry certain types of errors
			if isNonRetryableError(err) {
				return err
			}

			if attempt < config.MaxAttempts {
				delay = time.Duration(float64(delay) * config.Backoff)
				continue
			}
		} else {
			return nil // Success
		}
	}

	return fmt.Errorf("operation failed after %d attempts: %w", config.MaxAttempts, lastErr)
}

// isNonRetryableError determines if an error should not be retried
func isNonRetryableError(err error) bool {
	if err == nil {
		return false
	}

	// Don't retry validation errors or constraint violations
	errStr := strings.ToLower(err.Error())
	nonRetryablePatterns := []string{
		"constraint", "foreign key", "unique", "check constraint",
		"invalid input", "validation", "parse error",
	}

	for _, pattern := range nonRetryablePatterns {
		if strings.Contains(errStr, pattern) {
			return true
		}
	}

	return false
}

// withTimeout wraps context with timeout if not already set
func withTimeout(ctx context.Context, timeout time.Duration) (context.Context, context.CancelFunc) {
	if _, hasDeadline := ctx.Deadline(); hasDeadline {
		return ctx, func() {} // Context already has timeout
	}
	return context.WithTimeout(ctx, timeout)
}

// Save saves the session to the store with enhanced error handling
func (bs *BaseStore) Save(ctx context.Context, store GormStore, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		bs.TrackOperation("save", time.Since(start))
	}()

	ctx, cancel := withTimeout(ctx, DefaultOperationTimeout)
	defer cancel()

	operation := func() error {
		// Serialize session data
		data, err := bs.GetSerializer().Serialize(session)
		if err != nil {
			return fmt.Errorf("failed to serialize session: %w", err)
		}

		// Calculate expiry
		expiry := bs.CalculateExpiry(session)
		sessionKey := bs.GetSessionKey(session.ID)

		// Generate UUID for the session
		sessionUUID := uuid.New().String()

		// Extract and validate claims and redirect from session
		claims, err := extractClaims(session)
		if err != nil {
			return fmt.Errorf("failed to extract claims: %w", err)
		}

		redirect := extractRedirect(session)

		// Create GORM model
		proxySession := ProxySession{
			UUID:       sessionUUID,
			SessionKey: sessionKey,
			Data:       data,
			Expires:    &expiry,
			Expiring:   false,
			ProviderID: bs.ProviderID(),
			Claims:     string(claims),
			Redirect:   redirect,
		}

		// Use GORM's Upsert functionality with proper error handling
		result := store.GetDB().WithContext(ctx).Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "session_key"}, {Name: "provider_id"}},
			DoUpdates: clause.AssignmentColumns([]string{"data", "expires", "claims", "redirect", "updated_at"}),
		}).Create(&proxySession)

		if result.Error != nil {
			return fmt.Errorf("failed to save session to database: %w", result.Error)
		}

		return nil
	}

	return executeWithRetry(ctx, operation, DefaultRetryConfig())
}

// extractClaims safely extracts and marshals claims from session
func extractClaims(session *sessions.Session) ([]byte, error) {
	if c, ok := session.Values[constants.SessionClaims]; ok && c != nil {
		switch claimsValue := c.(type) {
		case string:
			// Claims already stored as JSON string
			return []byte(claimsValue), nil
		default:
			// Claims stored as struct, need to marshal
			claims, err := json.Marshal(claimsValue)
			if err != nil {
				return []byte("{}"), fmt.Errorf("failed to marshal claims: %w", err)
			}
			return claims, nil
		}
	}
	return []byte("{}"), nil
}

// extractRedirect safely extracts redirect from session
func extractRedirect(session *sessions.Session) string {
	if r, ok := session.Values[constants.SessionRedirect]; ok && r != nil {
		return fmt.Sprintf("%v", r)
	}
	return ""
}

// Load loads the session from the store with enhanced error handling
func (bs *BaseStore) Load(ctx context.Context, store GormStore, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		bs.TrackOperation("load", time.Since(start))
	}()

	ctx, cancel := withTimeout(ctx, DefaultOperationTimeout)
	defer cancel()

	operation := func() error {
		sessionKey := bs.GetSessionKey(session.ID)
		var proxySession ProxySession

		result := store.GetDB().WithContext(ctx).
			Where("session_key = ? AND provider_id = ? AND deleted_at IS NULL AND (expires IS NULL OR expires > "+store.NowValue()+")",
				sessionKey, bs.ProviderID()).
			First(&proxySession)

		if result.Error != nil {
			if errors.Is(result.Error, gorm.ErrRecordNotFound) {
				return gorm.ErrRecordNotFound // This is expected, don't wrap
			}
			return fmt.Errorf("failed to load session from database: %w", result.Error)
		}

		if err := bs.GetSerializer().Deserialize(proxySession.Data, session); err != nil {
			return fmt.Errorf("failed to deserialize session data: %w", err)
		}

		return nil
	}

	return executeWithRetry(ctx, operation, DefaultRetryConfig())
}

// Delete deletes the session from the store using soft delete with enhanced error handling
func (bs *BaseStore) Delete(ctx context.Context, store GormStore, session *sessions.Session) error {
	start := time.Now()
	defer func() {
		bs.TrackOperation("delete", time.Since(start))
	}()

	ctx, cancel := withTimeout(ctx, DefaultOperationTimeout)
	defer cancel()

	operation := func() error {
		sessionKey := bs.GetSessionKey(session.ID)

		// Soft delete by setting deleted_at timestamp instead of hard delete
		now := time.Now()
		result := store.GetDB().WithContext(ctx).
			Model(&ProxySession{}).
			Where("session_key = ? AND provider_id = ? AND deleted_at IS NULL", sessionKey, bs.ProviderID()).
			Update("deleted_at", now)

		if result.Error != nil {
			return fmt.Errorf("failed to delete session from database: %w", result.Error)
		}

		// Log the deletion operation for debugging
		log.WithFields(log.Fields{
			"session_id":    session.ID,
			"session_key":   sessionKey,
			"provider_id":   bs.ProviderID(),
			"rows_affected": result.RowsAffected,
		}).Info("Soft deleted session")

		if result.RowsAffected == 0 {
			log.WithFields(log.Fields{
				"session_id":  session.ID,
				"session_key": sessionKey,
				"provider_id": bs.ProviderID(),
			}).Warn("No rows affected by session deletion - session may not exist or already deleted")
		}

		return nil
	}

	return executeWithRetry(ctx, operation, DefaultRetryConfig())
}

// GetAllSessions returns all active sessions from the store with enhanced error handling
func (bs *BaseStore) GetAllSessions(ctx context.Context, store GormStore) ([]*sessions.Session, error) {
	ctx, cancel := withTimeout(ctx, DefaultOperationTimeout)
	defer cancel()

	var proxySessions []ProxySession
	var resultSessions []*sessions.Session
	var errs error

	operation := func() error {
		result := store.GetDB().WithContext(ctx).
			Where("provider_id = ? AND deleted_at IS NULL AND (expires IS NULL OR expires > "+store.NowValue()+")",
				bs.ProviderID()).
			Find(&proxySessions)

		if result.Error != nil {
			return fmt.Errorf("failed to retrieve sessions from database: %w", result.Error)
		}

		log.WithFields(log.Fields{
			"provider_id":    bs.ProviderID(),
			"sessions_found": len(proxySessions),
		}).Debug("Retrieved sessions from database")

		return nil
	}

	if err := executeWithRetry(ctx, operation, DefaultRetryConfig()); err != nil {
		return nil, err
	}

	// Process sessions outside retry loop to avoid duplicates
	for _, proxySession := range proxySessions {
		// Remove prefix from session key
		sessionID := strings.TrimPrefix(proxySession.SessionKey, bs.GetKeyPrefix())
		session := sessions.NewSession(store, "")
		session.ID = sessionID

		log.WithFields(log.Fields{
			"session_id":  sessionID,
			"session_key": proxySession.SessionKey,
			"provider_id": proxySession.ProviderID,
			"deleted_at":  proxySession.DeletedAt,
			"expires":     proxySession.Expires,
		}).Debug("Processing session for GetAllSessions")

		if err := bs.GetSerializer().Deserialize(proxySession.Data, session); err != nil {
			errs = multierr.Append(errs, fmt.Errorf("failed to deserialize session %s: %w", sessionID, err))
			continue
		}
		resultSessions = append(resultSessions, session)
	}

	log.WithFields(log.Fields{
		"provider_id":       bs.ProviderID(),
		"returned_sessions": len(resultSessions),
	}).Debug("Completed GetAllSessions")

	return resultSessions, errs
}
