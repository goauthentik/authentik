package config

import (
	"fmt"
	"log"
	"os"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConfigEnv(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", "bar"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_Scheme(t *testing.T) {
	assert.NoError(t, os.Setenv("foo", "bar"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", "env://foo"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

func TestConfigEnv_File(t *testing.T) {
	file, err := os.CreateTemp("", "")
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		assert.NoError(t, os.Remove(file.Name()))
	}()
	_, err = file.Write([]byte("bar"))
	if err != nil {
		panic(err)
	}

	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", fmt.Sprintf("file://%s", file.Name())))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "bar", Get().SecretKey)
}

// SQLite Configuration Tests
func TestConfigSQLiteDefaults(t *testing.T) {
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	// Test default values
	assert.Equal(t, "", Get().SQLite.Path)
	assert.Equal(t, 3600, Get().SQLite.CleanupInterval)
}

func TestConfigSQLitePath(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/tmp/test_sessions.sqlite"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, "/tmp/test_sessions.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteCleanupInterval(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "7200"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}
	assert.Equal(t, 7200, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteMultipleSettings(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/custom/path/sessions.sqlite"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "1800"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/custom/path/sessions.sqlite", Get().SQLite.Path)
	assert.Equal(t, 1800, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLitePathEnvScheme(t *testing.T) {
	assert.NoError(t, os.Setenv("SQLITE_PATH_VAR", "/env/path/sessions.sqlite"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "env://SQLITE_PATH_VAR"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/env/path/sessions.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("SQLITE_PATH_VAR"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLitePathFileScheme(t *testing.T) {
	file, err := os.CreateTemp("", "")
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		assert.NoError(t, os.Remove(file.Name()))
	}()
	_, err = file.Write([]byte("/file/path/sessions.sqlite"))
	if err != nil {
		panic(err)
	}

	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", fmt.Sprintf("file://%s", file.Name())))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/file/path/sessions.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteEmptyPath(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", ""))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteRelativePath(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "relative/path/sessions.sqlite"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "relative/path/sessions.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteAbsolutePath(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/absolute/path/sessions.sqlite"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/absolute/path/sessions.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteCleanupIntervalZero(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "0"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, 0, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteCleanupIntervalMinimum(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "60"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, 60, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteCleanupIntervalMaximum(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "604800"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, 604800, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteCleanupIntervalEnvScheme(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "3600"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, 3600, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteCleanupIntervalFileScheme(t *testing.T) {
	file, err := os.CreateTemp("", "")
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		assert.NoError(t, os.Remove(file.Name()))
	}()
	_, err = file.Write([]byte("9000"))
	if err != nil {
		panic(err)
	}

	// Close the file to ensure it's fully written
	file.Close()

	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", fmt.Sprintf("file://%s", file.Name())))
	cfg = nil
	c := Get()
	err = c.fromEnv()
	assert.NoError(t, err)

	assert.Equal(t, 9000, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteStructDefaultValues(t *testing.T) {
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "", Get().SQLite.Path)
	assert.Equal(t, 3600, Get().SQLite.CleanupInterval)
}

func TestConfigSQLiteStructAssignment(t *testing.T) {
	cfg = nil
	c := Get()
	c.SQLite.Path = "/custom/path.sqlite"
	c.SQLite.CleanupInterval = 7200

	assert.Equal(t, "/custom/path.sqlite", Get().SQLite.Path)
	assert.Equal(t, 7200, Get().SQLite.CleanupInterval)
}

func TestConfigSQLiteWithOtherSettings(t *testing.T) {
	// Test that SQLite settings don't interfere with other config settings
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/test/sqlite.db"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SECRET_KEY", "test-secret-key"))
	assert.NoError(t, os.Setenv("AUTHENTIK_LOG_LEVEL", "DEBUG"))

	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/test/sqlite.db", Get().SQLite.Path)
	assert.Equal(t, "test-secret-key", Get().SecretKey)
	assert.Equal(t, "DEBUG", Get().LogLevel)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SECRET_KEY"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_LOG_LEVEL"))
}

func TestConfigSQLitePathWithSpecialCharacters(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/path/with-special_chars!@#$.sqlite"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/path/with-special_chars!@#$.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLitePathWithSpaces(t *testing.T) {
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/path/with spaces/file.sqlite"))
	cfg = nil
	c := Get()
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/path/with spaces/file.sqlite", Get().SQLite.Path)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
}

func TestConfigSQLiteOverrideDefaults(t *testing.T) {
	// First set default values
	cfg = nil
	c := Get()
	c.SQLite.Path = "/default/path.sqlite"
	c.SQLite.CleanupInterval = 1800

	// Then override with environment variables
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/override/path.sqlite"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "3600"))

	// Apply environment variables
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/override/path.sqlite", Get().SQLite.Path)
	assert.Equal(t, 3600, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteEnvironmentPrecedence(t *testing.T) {
	// Test that environment variables take precedence over config file values
	cfg = nil
	c := Get()

	// Set initial values
	c.SQLite.Path = "/initial/path.sqlite"
	c.SQLite.CleanupInterval = 1200

	// Set environment variables
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", "/env/path.sqlite"))
	assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", "2400"))

	// Apply environment variables
	if err := c.fromEnv(); err != nil {
		panic(err)
	}

	assert.Equal(t, "/env/path.sqlite", Get().SQLite.Path)
	assert.Equal(t, 2400, Get().SQLite.CleanupInterval)

	// Clean up
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
	assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
}

func TestConfigSQLiteEdgeCases(t *testing.T) {
	testCases := []struct {
		name            string
		path            string
		cleanupValue    string
		expectedPath    string
		expectedCleanup int
	}{
		{
			name:            "Empty values",
			path:            "",
			cleanupValue:    "",
			expectedPath:    "",
			expectedCleanup: 3600, // Default value
		},
		{
			name:            "Invalid cleanup interval",
			path:            "/valid/path.sqlite",
			cleanupValue:    "not-a-number",
			expectedPath:    "/valid/path.sqlite",
			expectedCleanup: 3600, // Should keep default
		},
		{
			name:            "Very long path",
			path:            "/very/long/path/" + strings.Repeat("a", 200) + ".sqlite",
			cleanupValue:    "3600",
			expectedPath:    "/very/long/path/" + strings.Repeat("a", 200) + ".sqlite",
			expectedCleanup: 3600,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__PATH", tc.path))
			assert.NoError(t, os.Setenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL", tc.cleanupValue))

			cfg = nil
			c := Get()
			if err := c.fromEnv(); err != nil {
				panic(err)
			}

			assert.Equal(t, tc.expectedPath, Get().SQLite.Path)
			assert.Equal(t, tc.expectedCleanup, Get().SQLite.CleanupInterval)

			// Clean up
			assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__PATH"))
			assert.NoError(t, os.Unsetenv("AUTHENTIK_SQLITE__CLEANUP_INTERVAL"))
		})
	}
}
