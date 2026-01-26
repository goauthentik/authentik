package postgresstore

import (
	"context"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"goauthentik.io/internal/config"
)

func TestRefreshableConnPool_CredentialRefresh(t *testing.T) {
	// Create a temporary file for password rotation
	tmpDir := t.TempDir()
	passwordFile := filepath.Join(tmpDir, "db_password")

	cfg := config.Get()
	initialConfig := cfg.RefreshPostgreSQLConfig()

	// Determine the current database password as the baseline for the rotation test.
	initialPassword := initialConfig.Password
	if initialPassword == "" {
		initialPassword = "postgres"
	}

	err := os.WriteFile(passwordFile, []byte(initialPassword), 0600)
	require.NoError(t, err)

	// Set up config to use file:// URI for password
	originalPassword := os.Getenv("AUTHENTIK_POSTGRESQL__PASSWORD")
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "file://"+passwordFile))
	defer func() {
		if originalPassword != "" {
			_ = os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", originalPassword)
		} else {
			_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
		}
	}()

	// Reload config
	refreshedConfig := cfg.RefreshPostgreSQLConfig()

	// Build initial DSN
	dsn, err := BuildDSN(refreshedConfig)
	require.NoError(t, err)

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
	}

	// Create refreshable connection pool
	pool, err := NewRefreshableConnPool(dsn, gormConfig, 10, 100, time.Hour)
	require.NoError(t, err)
	defer func() { _ = pool.Close() }()

	// Test initial connection works
	ctx := context.Background()
	err = pool.Ping(ctx)
	assert.NoError(t, err, "Initial connection should work")

	// Create GORM DB
	db, err := pool.NewGORMDB()
	require.NoError(t, err)

	// Execute a test query
	var result int
	err = db.WithContext(ctx).Raw("SELECT 1").Scan(&result).Error
	assert.NoError(t, err, "Initial query should succeed")
	assert.Equal(t, 1, result)

	// Simulate password change by writing to file
	// In real scenario, this would be an external process updating the file
	time.Sleep(100 * time.Millisecond) // Small delay to ensure file modification time changes
	err = os.WriteFile(passwordFile, []byte(initialPassword), 0600)
	require.NoError(t, err)

	// Execute another query - should trigger credential refresh check
	err = db.WithContext(ctx).Raw("SELECT 2").Scan(&result).Error
	assert.NoError(t, err, "Query after credential refresh should succeed")
	assert.Equal(t, 2, result)
}

func TestRefreshableConnPool_Interfaces(t *testing.T) {
	// Verify that RefreshableConnPool implements required interfaces at compile time
	// This test will fail to compile if interfaces are not properly implemented
	var pool *RefreshableConnPool

	// Test gorm.ConnPool interface
	var _ gorm.ConnPool = pool

	// Test gorm.ConnPoolBeginner interface
	var _ gorm.ConnPoolBeginner = pool
}

func TestRefreshableConnPool_ConcurrentAccess(t *testing.T) {
	cfg := config.Get()
	dsn, err := BuildDSN(cfg.PostgreSQL)
	require.NoError(t, err)

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	}

	pool, err := NewRefreshableConnPool(dsn, gormConfig, 10, 100, time.Hour)
	require.NoError(t, err)
	defer func() { _ = pool.Close() }()

	db, err := pool.NewGORMDB()
	require.NoError(t, err)

	// Test that the connection is working
	ctx := context.Background()
	var result int
	err = db.WithContext(ctx).Raw("SELECT 1").Scan(&result).Error
	require.NoError(t, err, "Initial connection test should succeed")

	// Test concurrent queries
	numGoroutines := 10
	numQueries := 5

	var wg sync.WaitGroup
	errChan := make(chan error, numGoroutines*numQueries)

	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func(goroutineID int) {
			defer wg.Done()
			for j := 0; j < numQueries; j++ {
				var result int
				err := db.WithContext(ctx).Raw("SELECT 1").Scan(&result).Error
				if err != nil {
					errChan <- err
				}
			}
		}(i)
	}

	// Wait for all goroutines to complete, then close the channel
	wg.Wait()
	close(errChan)

	// Check for any errors
	for err := range errChan {
		assert.NoError(t, err, "Concurrent queries should succeed")
	}
}

func TestRefreshableConnPool_InvalidCredentials(t *testing.T) {
	// Create a pool with invalid credentials
	invalidDSN := "host=localhost port=5432 user=invalid password=invalid dbname=invalid sslmode=disable"

	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	}

	pool, err := NewRefreshableConnPool(invalidDSN, gormConfig, 10, 100, time.Hour)
	if err != nil {
		// sql.Open may succeed even with invalid credentials (lazy connection)
		return
	}
	defer func() { _ = pool.Close() }()

	// Ping should fail with invalid credentials
	ctx := context.Background()
	err = pool.Ping(ctx)
	assert.Error(t, err, "Ping with invalid credentials should fail")
}

func TestConfig_RefreshPostgreSQLConfig_FileURI(t *testing.T) {
	// Create temporary files for testing file:// URIs
	tmpDir := t.TempDir()

	passwordFile := filepath.Join(tmpDir, "password")
	userFile := filepath.Join(tmpDir, "user")
	hostFile := filepath.Join(tmpDir, "host")

	err := os.WriteFile(passwordFile, []byte("secret_password"), 0600)
	require.NoError(t, err)
	err = os.WriteFile(userFile, []byte("dbuser"), 0600)
	require.NoError(t, err)
	err = os.WriteFile(hostFile, []byte("db.example.com"), 0600)
	require.NoError(t, err)

	// Set up environment variables with file:// URIs
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "file://"+passwordFile))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__USER", "file://"+userFile))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "file://"+hostFile))
	defer func() {
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
	}()

	// Create and setup config
	cfg := &config.Config{}
	cfg.Setup()

	// Test initial values are parsed correctly
	assert.Equal(t, "secret_password", cfg.PostgreSQL.Password, "Initial password should be parsed from file")
	assert.Equal(t, "dbuser", cfg.PostgreSQL.User, "Initial user should be parsed from file")
	assert.Equal(t, "db.example.com", cfg.PostgreSQL.Host, "Initial host should be parsed from file")

	// Test RefreshPostgreSQLConfig returns same values initially
	refreshed := cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "secret_password", refreshed.Password)
	assert.Equal(t, "dbuser", refreshed.User)
	assert.Equal(t, "db.example.com", refreshed.Host)

	// Update password file (simulating credential rotation)
	err = os.WriteFile(passwordFile, []byte("new_password"), 0600)
	require.NoError(t, err)

	// Update user file
	err = os.WriteFile(userFile, []byte("new_dbuser"), 0600)
	require.NoError(t, err)

	// Refresh should pick up new values from files
	refreshed = cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "new_password", refreshed.Password, "Password should be refreshed from file")
	assert.Equal(t, "new_dbuser", refreshed.User, "User should be refreshed from file")

	// Original config struct should still have old values (not mutated)
	assert.Equal(t, "secret_password", cfg.PostgreSQL.Password, "Original config should not be mutated")
}

func TestConfig_RefreshPostgreSQLConfig_EnvURI(t *testing.T) {
	// Test with env:// URIs (referencing other env vars)
	require.NoError(t, os.Setenv("DB_PASSWORD", "env_password"))
	require.NoError(t, os.Setenv("DB_USER", "env_user"))
	require.NoError(t, os.Setenv("DB_HOST", "env_host"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "env://DB_PASSWORD"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__USER", "env://DB_USER"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "env://DB_HOST"))
	defer func() {
		_ = os.Unsetenv("DB_PASSWORD")
		_ = os.Unsetenv("DB_USER")
		_ = os.Unsetenv("DB_HOST")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
	}()

	cfg := &config.Config{}
	cfg.Setup()

	// Test initial values are parsed correctly
	assert.Equal(t, "env_password", cfg.PostgreSQL.Password, "Initial password should be parsed from env")
	assert.Equal(t, "env_user", cfg.PostgreSQL.User, "Initial user should be parsed from env")
	assert.Equal(t, "env_host", cfg.PostgreSQL.Host, "Initial host should be parsed from env")

	// Test RefreshPostgreSQLConfig
	refreshed := cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "env_password", refreshed.Password)
	assert.Equal(t, "env_user", refreshed.User)
	assert.Equal(t, "env_host", refreshed.Host)

	// Change referenced environment variables (simulating credential rotation)
	require.NoError(t, os.Setenv("DB_PASSWORD", "new_env_password"))
	require.NoError(t, os.Setenv("DB_USER", "new_env_user"))

	// Refresh should pick up new values
	refreshed = cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "new_env_password", refreshed.Password, "Password should be refreshed from env")
	assert.Equal(t, "new_env_user", refreshed.User, "User should be refreshed from env")

	// Original config struct should still have old values (not mutated)
	assert.Equal(t, "env_password", cfg.PostgreSQL.Password, "Original config should not be mutated")
}

func TestConfig_RefreshPostgreSQLConfig_PlainValues(t *testing.T) {
	// Test with plain values (no URI scheme)
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "plain_password"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__USER", "plain_user"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "localhost"))
	defer func() {
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
	}()

	cfg := &config.Config{}
	cfg.Setup()

	// Test initial values
	assert.Equal(t, "plain_password", cfg.PostgreSQL.Password)
	assert.Equal(t, "plain_user", cfg.PostgreSQL.User)
	assert.Equal(t, "localhost", cfg.PostgreSQL.Host)

	// Test refresh returns same values
	refreshed := cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "plain_password", refreshed.Password)
	assert.Equal(t, "plain_user", refreshed.User)
	assert.Equal(t, "localhost", refreshed.Host)

	// Change env vars
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "new_plain_password"))

	// Refresh should pick up new plain value
	refreshed = cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "new_plain_password", refreshed.Password, "Plain password should be refreshed")
}

func TestConfig_RefreshPostgreSQLConfig_MixedSources(t *testing.T) {
	// Test with mixed sources: file://, env://, and plain
	tmpDir := t.TempDir()
	passwordFile := filepath.Join(tmpDir, "password")
	err := os.WriteFile(passwordFile, []byte("file_password"), 0600)
	require.NoError(t, err)

	require.NoError(t, os.Setenv("DB_USER_VAR", "env_user"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "file://"+passwordFile))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__USER", "env://DB_USER_VAR"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "plain_host"))
	defer func() {
		_ = os.Unsetenv("DB_USER_VAR")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
		_ = os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
	}()

	cfg := &config.Config{}
	cfg.Setup()

	// Test initial values
	assert.Equal(t, "file_password", cfg.PostgreSQL.Password)
	assert.Equal(t, "env_user", cfg.PostgreSQL.User)
	assert.Equal(t, "plain_host", cfg.PostgreSQL.Host)

	// Update all sources
	err = os.WriteFile(passwordFile, []byte("new_file_password"), 0600)
	require.NoError(t, err)
	require.NoError(t, os.Setenv("DB_USER_VAR", "new_env_user"))
	require.NoError(t, os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "new_plain_host"))

	// Refresh should pick up all changes
	refreshed := cfg.RefreshPostgreSQLConfig()
	assert.Equal(t, "new_file_password", refreshed.Password, "File password should be refreshed")
	assert.Equal(t, "new_env_user", refreshed.User, "Env user should be refreshed")
	assert.Equal(t, "new_plain_host", refreshed.Host, "Plain host should be refreshed")
}

func TestIsAuthError(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
		{
			name:     "generic error",
			err:      assert.AnError,
			expected: false,
		},
		{
			name: "postgres error code 28000 - invalid_authorization_specification",
			err: &pgconn.PgError{
				Code:    "28000",
				Message: "invalid authorization specification",
			},
			expected: true,
		},
		{
			name: "postgres error code 28P01 - invalid_password",
			err: &pgconn.PgError{
				Code:    "28P01",
				Message: "password authentication failed for user",
			},
			expected: true,
		},
		{
			name: "postgres error code 28P02 - invalid_password (deprecated)",
			err: &pgconn.PgError{
				Code:    "28P02",
				Message: "invalid password",
			},
			expected: true,
		},
		{
			name: "postgres error code 42P01 - undefined_table (not auth error)",
			err: &pgconn.PgError{
				Code:    "42P01",
				Message: "relation does not exist",
			},
			expected: false,
		},
		{
			name: "postgres error code 23505 - unique_violation (not auth error)",
			err: &pgconn.PgError{
				Code:    "23505",
				Message: "duplicate key value violates unique constraint",
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isAuthError(tt.err)
			assert.Equal(t, tt.expected, result)
		})
	}
}
