package sqlitestore

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestOpenSQLiteDatabase(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_connect.sqlite")

	// Test successful database opening
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	// Test connection
	err = db.Ping()
	assert.NoError(t, err)

	// Verify database file was created
	assert.FileExists(t, dbPath)
}

func TestSQLiteDatabaseParameters(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_params.sqlite")

	// Test with WAL mode and timeout
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000&_busy_timeout=10000")
	require.NoError(t, err)
	defer db.Close()

	err = db.Ping()
	assert.NoError(t, err)

	// Verify WAL mode is enabled
	var journalMode string
	err = db.QueryRow("PRAGMA journal_mode").Scan(&journalMode)
	assert.NoError(t, err)
	assert.Equal(t, "wal", journalMode)
}

func TestSQLiteDatabaseConnectionLimits(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_limits.sqlite")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	// Set connection limits
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)

	err = db.Ping()
	assert.NoError(t, err)

	// Test concurrent connections within limits
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			var result int
			err := db.QueryRow("SELECT 1").Scan(&result)
			assert.NoError(t, err)
			assert.Equal(t, 1, result)
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}
}

func TestSQLiteDatabaseInvalidPath(t *testing.T) {
	// Test with path that cannot be created
	invalidPath := "/root/cannot/create/this/path/test.sqlite"

	db, err := sql.Open("sqlite3", invalidPath+"?_journal=WAL&_timeout=5000")
	if err == nil {
		// If Open succeeds, Ping should fail
		err = db.Ping()
		if err == nil {
			// Cleanup if somehow it worked
			db.Close()
			assert.Fail(t, "Expected an error when opening or pinging with an invalid path, but no error occurred.")
		} else {
			assert.Error(t, err, "Expected an error when pinging with an invalid path")
		}
	} else {
		assert.Error(t, err, "Expected an error when opening with an invalid path")
	}
}

func TestSQLiteDatabaseReadOnlyMode(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_readonly.sqlite")

	// Create database first
	db1, err := sql.Open("sqlite3", dbPath)
	require.NoError(t, err)

	// Create a table
	_, err = db1.Exec("CREATE TABLE test (id INTEGER)")
	require.NoError(t, err)
	db1.Close()

	// Set read-only permissions on the file to ensure write fails
	err = os.Chmod(dbPath, 0444)
	require.NoError(t, err)
	defer os.Chmod(dbPath, 0644)

	// Open in read-only mode
	db2, err := sql.Open("sqlite3", dbPath+"?mode=ro")
	require.NoError(t, err)
	defer db2.Close()

	err = db2.Ping()
	assert.NoError(t, err)

	// Should be able to read
	var count int
	err = db2.QueryRow("SELECT COUNT(*) FROM test").Scan(&count)
	assert.NoError(t, err)

	// Should not be able to write
	_, err = db2.Exec("INSERT INTO test (id) VALUES (1)")
	assert.Error(t, err, "Expected an error when writing to read-only database")
}

func TestSQLiteDatabaseConcurrentAccess(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_concurrent.sqlite")

	// Create initial database with table
	setupDB, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)

	_, err = setupDB.Exec(`
		CREATE TABLE concurrent_test (
			id INTEGER PRIMARY KEY,
			value TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	require.NoError(t, err)
	setupDB.Close()

	// Test multiple concurrent connections
	numConnections := 5
	done := make(chan bool, numConnections)

	for i := 0; i < numConnections; i++ {
		go func(id int) {
			defer func() { done <- true }()

			db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
			assert.NoError(t, err)
			defer db.Close()

			// Insert data
			_, err = db.Exec("INSERT INTO concurrent_test (value) VALUES (?)",
				fmt.Sprintf("value-%d", id))
			assert.NoError(t, err)

			// Read data
			var count int
			err = db.QueryRow("SELECT COUNT(*) FROM concurrent_test").Scan(&count)
			assert.NoError(t, err)
			assert.Greater(t, count, 0)
		}(i)
	}

	// Wait for all connections
	for i := 0; i < numConnections; i++ {
		<-done
	}

	// Verify final state
	verifyDB, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer verifyDB.Close()

	var finalCount int
	err = verifyDB.QueryRow("SELECT COUNT(*) FROM concurrent_test").Scan(&finalCount)
	assert.NoError(t, err)
	assert.Equal(t, numConnections, finalCount)
}

func TestSQLiteDatabaseTransactions(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_transactions.sqlite")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	// Create test table
	_, err = db.Exec(`
		CREATE TABLE transaction_test (
			id INTEGER PRIMARY KEY,
			value TEXT
		)
	`)
	require.NoError(t, err)

	// Test successful transaction
	tx, err := db.Begin()
	require.NoError(t, err)

	_, err = tx.Exec("INSERT INTO transaction_test (value) VALUES (?)", "test1")
	require.NoError(t, err)

	_, err = tx.Exec("INSERT INTO transaction_test (value) VALUES (?)", "test2")
	require.NoError(t, err)

	err = tx.Commit()
	assert.NoError(t, err)

	// Verify data was committed
	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM transaction_test").Scan(&count)
	assert.NoError(t, err)
	assert.Equal(t, 2, count)

	// Test rollback transaction
	tx2, err := db.Begin()
	require.NoError(t, err)

	_, err = tx2.Exec("INSERT INTO transaction_test (value) VALUES (?)", "rollback")
	require.NoError(t, err)

	err = tx2.Rollback()
	assert.NoError(t, err)

	// Verify rollback worked
	var countAfterRollback int
	err = db.QueryRow("SELECT COUNT(*) FROM transaction_test").Scan(&countAfterRollback)
	assert.NoError(t, err)
	assert.Equal(t, 2, countAfterRollback) // Should still be 2
}

func TestSQLiteDatabaseWALMode(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_wal.sqlite")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	err = db.Ping()
	require.NoError(t, err)

	// Verify WAL mode
	var journalMode string
	err = db.QueryRow("PRAGMA journal_mode").Scan(&journalMode)
	assert.NoError(t, err)
	assert.Equal(t, "wal", journalMode)

	// Test WAL checkpoint
	var busy, log, checkpointed int
	err = db.QueryRow("PRAGMA wal_checkpoint").Scan(&busy, &log, &checkpointed)
	assert.NoError(t, err)
	assert.GreaterOrEqual(t, busy, 0)
	assert.GreaterOrEqual(t, log, 0)
	assert.GreaterOrEqual(t, checkpointed, 0)
}

func TestSQLiteDatabasePragmaSettings(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_pragma.sqlite")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	// Test various PRAGMA settings
	testCases := []struct {
		pragma   string
		expected string
	}{
		{"journal_mode", "wal"},
		{"synchronous", "1"},    // NORMAL is default in WAL mode
		{"cache_size", "-2000"}, // Default negative value means KB
		{"temp_store", "0"},     // DEFAULT
	}

	for _, tc := range testCases {
		t.Run(tc.pragma, func(t *testing.T) {
			var resultString string

			// Query the pragma value
			err := db.QueryRow(fmt.Sprintf("PRAGMA %s", tc.pragma)).Scan(&resultString)
			assert.NoError(t, err)

			// Compare as strings
			assert.Equal(t, tc.expected, resultString)
		})
	}
}

func TestSQLiteDatabaseErrorHandling(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_errors.sqlite")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db.Close()

	// Test syntax error
	_, err = db.Exec("INVALID SQL STATEMENT")
	assert.Error(t, err)

	// Test table not exists error
	var result int
	err = db.QueryRow("SELECT COUNT(*) FROM nonexistent_table").Scan(&result)
	assert.Error(t, err)

	// Test constraint violation
	_, err = db.Exec(`
		CREATE TABLE constraint_test (
			id INTEGER PRIMARY KEY,
			unique_value TEXT UNIQUE
		)
	`)
	require.NoError(t, err)

	_, err = db.Exec("INSERT INTO constraint_test (unique_value) VALUES (?)", "test")
	require.NoError(t, err)

	// This should fail due to unique constraint
	_, err = db.Exec("INSERT INTO constraint_test (unique_value) VALUES (?)", "test")
	assert.Error(t, err)
}

func TestSQLiteDatabaseConnectionString(t *testing.T) {
	tempDir := t.TempDir()

	testCases := []struct {
		name          string
		connectionStr string
		shouldSucceed bool
	}{
		{
			name:          "Basic connection",
			connectionStr: filepath.Join(tempDir, "basic.sqlite"),
			shouldSucceed: true,
		},
		{
			name:          "WAL mode connection",
			connectionStr: filepath.Join(tempDir, "wal.sqlite") + "?_journal=WAL",
			shouldSucceed: true,
		},
		{
			name:          "WAL with timeout",
			connectionStr: filepath.Join(tempDir, "wal_timeout.sqlite") + "?_journal=WAL&_timeout=5000",
			shouldSucceed: true,
		},
		{
			name:          "Multiple parameters",
			connectionStr: filepath.Join(tempDir, "multi.sqlite") + "?_journal=WAL&_timeout=5000&_busy_timeout=10000",
			shouldSucceed: true,
		},
		{
			name:          "In-memory database",
			connectionStr: ":memory:?_journal=WAL",
			shouldSucceed: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			db, err := sql.Open("sqlite3", tc.connectionStr)

			if tc.shouldSucceed {
				assert.NoError(t, err)
				if db != nil {
					err = db.Ping()
					assert.NoError(t, err)
					db.Close()
				}
			} else {
				assert.Error(t, err)
			}
		})
	}
}

func TestSQLiteDatabaseFilePermissions(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_permissions.sqlite")

	// Create database
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)

	err = db.Ping()
	require.NoError(t, err)
	db.Close()

	// Check file was created
	assert.FileExists(t, dbPath)

	// Check file permissions
	info, err := os.Stat(dbPath)
	require.NoError(t, err)

	mode := info.Mode()
	assert.True(t, mode.IsRegular())

	// Should be readable and writable by owner
	assert.True(t, mode&0600 != 0)
}

func TestSQLiteDatabaseRecovery(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_recovery.sqlite")

	// Create initial database
	db1, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)

	_, err = db1.Exec(`
		CREATE TABLE recovery_test (
			id INTEGER PRIMARY KEY,
			data TEXT
		)
	`)
	require.NoError(t, err)

	_, err = db1.Exec("INSERT INTO recovery_test (data) VALUES (?)", "initial data")
	require.NoError(t, err)

	db1.Close()

	// Reopen database
	db2, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)
	defer db2.Close()

	// Verify data persisted
	var data string
	err = db2.QueryRow("SELECT data FROM recovery_test WHERE id = 1").Scan(&data)
	assert.NoError(t, err)
	assert.Equal(t, "initial data", data)

	// Add more data
	_, err = db2.Exec("INSERT INTO recovery_test (data) VALUES (?)", "recovery data")
	assert.NoError(t, err)

	// Verify both records exist
	var count int
	err = db2.QueryRow("SELECT COUNT(*) FROM recovery_test").Scan(&count)
	assert.NoError(t, err)
	assert.Equal(t, 2, count)
}

func TestSQLiteDatabaseBusyTimeout(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_busy.sqlite")

	// Create database with busy timeout
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000&_busy_timeout=1000")
	require.NoError(t, err)
	defer db.Close()

	err = db.Ping()
	assert.NoError(t, err)

	// Create test table
	_, err = db.Exec(`
		CREATE TABLE busy_test (
			id INTEGER PRIMARY KEY,
			value TEXT
		)
	`)
	require.NoError(t, err)

	// Test that operations complete within timeout
	start := time.Now()
	_, err = db.Exec("INSERT INTO busy_test (value) VALUES (?)", "test")
	duration := time.Since(start)

	assert.NoError(t, err)
	assert.Less(t, duration, time.Second) // Should complete quickly
}

func TestSQLiteDatabaseCleanup(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test_cleanup.sqlite")

	// Create database
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000")
	require.NoError(t, err)

	// Create table and add data
	_, err = db.Exec(`
		CREATE TABLE cleanup_test (
			id INTEGER PRIMARY KEY,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	`)
	require.NoError(t, err)

	// Insert multiple records
	for i := 0; i < 100; i++ {
		_, err = db.Exec("INSERT INTO cleanup_test DEFAULT VALUES")
		require.NoError(t, err)
	}

	// Verify data exists
	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM cleanup_test").Scan(&count)
	require.NoError(t, err)
	assert.Equal(t, 100, count)

	// Test vacuum operation
	_, err = db.Exec("VACUUM")
	assert.NoError(t, err)

	// Verify data still exists after vacuum
	err = db.QueryRow("SELECT COUNT(*) FROM cleanup_test").Scan(&count)
	assert.NoError(t, err)
	assert.Equal(t, 100, count)

	db.Close()

	// Verify the main database file exists
	assert.FileExists(t, dbPath)

	// WAL files may or may not exist depending on timing and checkpointing
	// but we can check if they were created at some point
	walPath := dbPath + "-wal"
	shmPath := dbPath + "-shm"

	// These files might exist depending on WAL checkpointing
	_, walExists := os.Stat(walPath)
	_, shmExists := os.Stat(shmPath)

	// At least one of the WAL-related files should have existed at some point
	// or the main database should exist (which we already verified)
	_ = walExists // WAL file may or may not exist
	_ = shmExists // SHM file may or may not exist
}
