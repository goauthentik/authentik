package postgresstore

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"strings"
	"sync"
	"time"

	log "github.com/sirupsen/logrus"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	"goauthentik.io/internal/config"
)

// RefreshableConnPool wraps sql.DB and refreshes PostgreSQL credentials on authentication errors
// This implements gorm.ConnPool interface to allow credential rotation
type RefreshableConnPool struct {
	mu         sync.RWMutex
	db         *sql.DB
	dsnBuilder func(config.PostgreSQLConfig) (string, error)
	log        *log.Entry
	currentDSN string
	gormConfig *gorm.Config

	// Connection pool settings (stored for reapplication after reconnection)
	maxIdleConns    int
	maxOpenConns    int
	connMaxLifetime time.Duration

	// Reconnection management
	reconnecting sync.Mutex // Prevent concurrent reconnections
}

// NewRefreshableConnPool creates a new connection pool that refreshes credentials from config
func NewRefreshableConnPool(initialDSN string, gormConfig *gorm.Config, maxIdleConns, maxOpenConns int, connMaxLifetime time.Duration) (*RefreshableConnPool, error) {
	db, err := sql.Open("postgres", initialDSN)
	if err != nil {
		return nil, err
	}

	// Apply connection pool settings
	db.SetMaxIdleConns(maxIdleConns)
	db.SetMaxOpenConns(maxOpenConns)
	db.SetConnMaxLifetime(connMaxLifetime)

	pool := &RefreshableConnPool{
		db:              db,
		dsnBuilder:      BuildDSN,
		log:             log.WithField("logger", "authentik.outpost.proxyv2.postgresstore.connpool"),
		currentDSN:      initialDSN,
		gormConfig:      gormConfig,
		maxIdleConns:    maxIdleConns,
		maxOpenConns:    maxOpenConns,
		connMaxLifetime: connMaxLifetime,
	}

	return pool, nil
}

// isAuthError checks if an error is a PostgreSQL authentication error
// This checks for common authentication error patterns in the error message
func isAuthError(err error) bool {
	if err == nil {
		return false
	}

	// Check for common authentication error message patterns
	// These patterns match PostgreSQL error codes:
	// 28P01: invalid_password
	// 28000: invalid_authorization_specification
	// 28P02: invalid_password (deprecated but still used)
	errMsg := strings.ToLower(err.Error())
	return strings.Contains(errMsg, "password authentication failed") ||
		strings.Contains(errMsg, "no password supplied") ||
		strings.Contains(errMsg, "invalid authorization specification") ||
		strings.Contains(errMsg, "pq: password authentication failed") ||
		strings.Contains(errMsg, "authentication failed") ||
		strings.Contains(errMsg, "28p01") || // PostgreSQL error code
		strings.Contains(errMsg, "28000") || // PostgreSQL error code
		strings.Contains(errMsg, "28p02") // PostgreSQL error code (deprecated)
}

// refreshCredentials checks if credentials have changed and reconnects if needed
func (p *RefreshableConnPool) refreshCredentials(ctx context.Context) error {
	// Prevent concurrent reconnections
	p.reconnecting.Lock()
	defer p.reconnecting.Unlock()

	// Get fresh config
	cfg := config.Get().RefreshPostgreSQLConfig()
	newDSN, err := p.dsnBuilder(cfg)
	if err != nil {
		p.log.WithError(err).Warn("Failed to build DSN with refreshed credentials")
		return err
	}

	p.mu.RLock()
	dsnChanged := newDSN != p.currentDSN
	p.mu.RUnlock()

	if !dsnChanged {
		p.log.Debug("Credentials unchanged, skipping reconnection")
		return nil
	}

	p.mu.Lock()
	defer p.mu.Unlock()

	// Double-check after acquiring write lock
	if newDSN == p.currentDSN {
		return nil
	}

	p.log.Info("PostgreSQL credentials changed, reconnecting...")

	// Close old connection
	oldDB := p.db
	if oldDB != nil {
		if err := oldDB.Close(); err != nil {
			p.log.WithError(err).Warn("Failed to close old database connection")
		}
	}

	// Open new connection with fresh credentials
	newDB, err := sql.Open("postgres", newDSN)
	if err != nil {
		p.log.WithError(err).Error("Failed to open new database connection with refreshed credentials")
		return err
	}

	// Reapply connection pool settings
	newDB.SetMaxIdleConns(p.maxIdleConns)
	newDB.SetMaxOpenConns(p.maxOpenConns)
	newDB.SetConnMaxLifetime(p.connMaxLifetime)

	// Verify the connection works
	if err := newDB.PingContext(ctx); err != nil {
		p.log.WithError(err).Error("Failed to ping database with new credentials")
		_ = newDB.Close()
		return err
	}

	p.db = newDB
	p.currentDSN = newDSN
	p.log.Info("Successfully reconnected with new PostgreSQL credentials")

	return nil
}

// tryWithRefresh attempts an operation, and if it fails with an auth error, refreshes credentials and retries
func (p *RefreshableConnPool) tryWithRefresh(ctx context.Context, op func() error) error {
	err := op()
	if err != nil && isAuthError(err) {
		p.log.WithError(err).Info("Authentication error detected, attempting to refresh credentials")
		if refreshErr := p.refreshCredentials(ctx); refreshErr == nil {
			// Retry the operation once after successful refresh
			p.log.Debug("Retrying operation after credential refresh")
			return op()
		} else {
			p.log.WithError(refreshErr).Warn("Failed to refresh credentials, returning original error")
		}
	}
	return err
}

// PrepareContext implements gorm.ConnPool interface
func (p *RefreshableConnPool) PrepareContext(ctx context.Context, query string) (*sql.Stmt, error) {
	var stmt *sql.Stmt
	err := p.tryWithRefresh(ctx, func() error {
		p.mu.RLock()
		defer p.mu.RUnlock()
		var err error
		stmt, err = p.db.PrepareContext(ctx, query)
		return err
	})
	return stmt, err
}

// ExecContext implements gorm.ConnPool interface
func (p *RefreshableConnPool) ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	var result sql.Result
	err := p.tryWithRefresh(ctx, func() error {
		p.mu.RLock()
		defer p.mu.RUnlock()
		var err error
		result, err = p.db.ExecContext(ctx, query, args...)
		return err
	})
	return result, err
}

// QueryContext implements gorm.ConnPool interface
func (p *RefreshableConnPool) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	var rows *sql.Rows
	err := p.tryWithRefresh(ctx, func() error {
		p.mu.RLock()
		defer p.mu.RUnlock()
		var err error
		rows, err = p.db.QueryContext(ctx, query, args...)
		return err
	})
	return rows, err
}

// QueryRowContext implements gorm.ConnPool interface
func (p *RefreshableConnPool) QueryRowContext(ctx context.Context, query string, args ...interface{}) *sql.Row {
	// Note: sql.Row doesn't return errors until Scan() is called, so we can't detect auth errors here
	// The error will be caught in higher-level GORM operations
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.db.QueryRowContext(ctx, query, args...)
}

// BeginTx implements gorm.TxBeginner and gorm.ConnPoolBeginner interfaces
func (p *RefreshableConnPool) BeginTx(ctx context.Context, opts *sql.TxOptions) (gorm.ConnPool, error) {
	var tx *sql.Tx
	err := p.tryWithRefresh(ctx, func() error {
		p.mu.RLock()
		defer p.mu.RUnlock()
		var err error
		tx, err = p.db.BeginTx(ctx, opts)
		return err
	})
	if err != nil {
		return nil, err
	}
	return &refreshableTx{Tx: tx, pool: p}, nil
}

// refreshableTx wraps sql.Tx to implement gorm.ConnPool
type refreshableTx struct {
	*sql.Tx
	pool *RefreshableConnPool
}

func (tx *refreshableTx) PrepareContext(ctx context.Context, query string) (*sql.Stmt, error) {
	return tx.Tx.PrepareContext(ctx, query)
}

func (tx *refreshableTx) ExecContext(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return tx.Tx.ExecContext(ctx, query, args...)
}

func (tx *refreshableTx) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return tx.Tx.QueryContext(ctx, query, args...)
}

func (tx *refreshableTx) QueryRowContext(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return tx.Tx.QueryRowContext(ctx, query, args...)
}

// Close closes the underlying database connection
func (p *RefreshableConnPool) Close() error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.db != nil {
		return p.db.Close()
	}
	return nil
}

// Ping verifies the connection is alive
func (p *RefreshableConnPool) Ping(ctx context.Context) error {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.db.PingContext(ctx)
}

// GetDB returns the underlying sql.DB for connection pool configuration
func (p *RefreshableConnPool) GetDB() *sql.DB {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.db
}

// NewGORMDB creates a GORM DB instance using the refreshable connection pool
func (p *RefreshableConnPool) NewGORMDB() (*gorm.DB, error) {
	dialector := postgres.New(postgres.Config{
		Conn: p,
	})
	return gorm.Open(dialector, p.gormConfig)
}

// Ensure RefreshableConnPool implements required interfaces
var (
	_ gorm.ConnPool         = (*RefreshableConnPool)(nil)
	_ gorm.ConnPoolBeginner = (*RefreshableConnPool)(nil)
	_ driver.Pinger         = (*RefreshableConnPool)(nil)
)
