package pgstore

import (
	"os"
	"testing"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoadPostgreSQLConfig(t *testing.T) {
	// Save original environment
	originalEnv := map[string]string{
		"AUTHENTIK_POSTGRESQL__HOST":        os.Getenv("AUTHENTIK_POSTGRESQL__HOST"),
		"AUTHENTIK_POSTGRESQL__PORT":        os.Getenv("AUTHENTIK_POSTGRESQL__PORT"),
		"AUTHENTIK_POSTGRESQL__NAME":        os.Getenv("AUTHENTIK_POSTGRESQL__NAME"),
		"AUTHENTIK_POSTGRESQL__USER":        os.Getenv("AUTHENTIK_POSTGRESQL__USER"),
		"AUTHENTIK_POSTGRESQL__PASSWORD":    os.Getenv("AUTHENTIK_POSTGRESQL__PASSWORD"),
		"AUTHENTIK_POSTGRESQL__SSLMODE":     os.Getenv("AUTHENTIK_POSTGRESQL__SSLMODE"),
		"AUTHENTIK_POSTGRESQL__SSLROOTCERT": os.Getenv("AUTHENTIK_POSTGRESQL__SSLROOTCERT"),
		"AUTHENTIK_POSTGRESQL__SSLCERT":     os.Getenv("AUTHENTIK_POSTGRESQL__SSLCERT"),
		"AUTHENTIK_POSTGRESQL__SSLKEY":      os.Getenv("AUTHENTIK_POSTGRESQL__SSLKEY"),
	}

	// Restore environment after test
	defer func() {
		for k, v := range originalEnv {
			if v == "" {
				os.Unsetenv(k)
			} else {
				os.Setenv(k, v)
			}
		}
	}()

	// Test with environment variables set
	os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "testhost")
	os.Setenv("AUTHENTIK_POSTGRESQL__PORT", "5433")
	os.Setenv("AUTHENTIK_POSTGRESQL__NAME", "testdb")
	os.Setenv("AUTHENTIK_POSTGRESQL__USER", "testuser")
	os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "testpass")
	os.Setenv("AUTHENTIK_POSTGRESQL__SSLMODE", "require")
	os.Setenv("AUTHENTIK_POSTGRESQL__SSLROOTCERT", "/path/to/ca.crt")
	os.Setenv("AUTHENTIK_POSTGRESQL__SSLCERT", "/path/to/client.crt")
	os.Setenv("AUTHENTIK_POSTGRESQL__SSLKEY", "/path/to/client.key")

	config := LoadPostgreSQLConfig()

	assert.Equal(t, "testhost", config.Host)
	assert.Equal(t, 5433, config.Port)
	assert.Equal(t, "testdb", config.Database)
	assert.Equal(t, "testuser", config.User)
	assert.Equal(t, "testpass", config.Password)
	assert.Equal(t, "require", config.SSLMode)
	assert.Equal(t, "/path/to/ca.crt", config.SSLRootCert)
	assert.Equal(t, "/path/to/client.crt", config.SSLCert)
	assert.Equal(t, "/path/to/client.key", config.SSLKey)
}

func TestLoadPostgreSQLConfig_DefaultValues(t *testing.T) {
	// Clear environment variables
	os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__PORT")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__NAME")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__PASSWORD")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__SSLMODE")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__SSLROOTCERT")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__SSLCERT")
	os.Unsetenv("AUTHENTIK_POSTGRESQL__SSLKEY")

	config := LoadPostgreSQLConfig()

	// These should be defaults from the config system
	assert.Equal(t, "", config.Host)
	assert.Equal(t, 0, config.Port)
	assert.Equal(t, "", config.Database)
	assert.Equal(t, "", config.User)
	assert.Equal(t, "", config.Password)
	assert.Equal(t, "", config.SSLMode)
	assert.Equal(t, "", config.SSLRootCert)
	assert.Equal(t, "", config.SSLCert)
	assert.Equal(t, "", config.SSLKey)
}

func TestPostgreSQLConnectionConfig_ValidateConfig(t *testing.T) {
	logger := log.WithField("test", "validate")

	t.Run("Valid config", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
			SSLMode:  "disable",
		}

		err := config.ValidateConfig(logger)
		assert.NoError(t, err)
	})

	t.Run("Missing host", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [host]")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__HOST")
	})

	t.Run("Missing user", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			Password: "password",
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [user]")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__USER")
	})

	t.Run("Missing database", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			User:     "authentik",
			Password: "password",
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [database]")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__NAME")
	})

	t.Run("Multiple missing fields", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Port:     5432,
			Password: "password",
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [host user database]")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__HOST")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__USER")
		assert.Contains(t, err.Error(), "AUTHENTIK_POSTGRESQL__NAME")
	})

	t.Run("Missing password warning", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			// Password is empty
		}

		err := config.ValidateConfig(logger)
		assert.NoError(t, err) // Password is not required for validation to pass
	})

	t.Run("With SSL certificates", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:        "localhost",
			Port:        5432,
			Database:    "authentik",
			User:        "authentik",
			Password:    "password",
			SSLMode:     "require",
			SSLRootCert: "/path/to/ca.crt",
			SSLCert:     "/path/to/client.crt",
			SSLKey:      "/path/to/client.key",
		}

		err := config.ValidateConfig(logger)
		assert.NoError(t, err)
	})
}

func TestPostgreSQLConnectionConfig_BuildConnectionString(t *testing.T) {
	t.Run("Basic connection string", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password=password"
		assert.Equal(t, expected, connStr)
	})

	t.Run("With SSL mode", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
			SSLMode:  "require",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password=password sslmode=require"
		assert.Equal(t, expected, connStr)
	})

	t.Run("With SSL certificates", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:        "localhost",
			Port:        5432,
			Database:    "authentik",
			User:        "authentik",
			Password:    "password",
			SSLMode:     "require",
			SSLRootCert: "/path/to/ca.crt",
			SSLCert:     "/path/to/client.crt",
			SSLKey:      "/path/to/client.key",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password=password sslmode=require sslrootcert=/path/to/ca.crt sslcert=/path/to/client.crt sslkey=/path/to/client.key"
		assert.Equal(t, expected, connStr)
	})

	t.Run("With empty password", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password="
		assert.Equal(t, expected, connStr)
	})

	t.Run("With special characters in password", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik",
			User:     "authentik",
			Password: "pass@word!123",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password=pass@word!123"
		assert.Equal(t, expected, connStr)
	})

	t.Run("With custom port", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "pg.example.com",
			Port:     5433,
			Database: "myapp",
			User:     "myuser",
			Password: "mypass",
		}

		connStr := config.BuildConnectionString()
		expected := "host=pg.example.com port=5433 dbname=myapp user=myuser password=mypass"
		assert.Equal(t, expected, connStr)
	})

	t.Run("Partial SSL config", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:        "localhost",
			Port:        5432,
			Database:    "authentik",
			User:        "authentik",
			Password:    "password",
			SSLMode:     "require",
			SSLRootCert: "/path/to/ca.crt",
			// SSLCert and SSLKey are empty
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik user=authentik password=password sslmode=require sslrootcert=/path/to/ca.crt"
		assert.Equal(t, expected, connStr)
	})
}

func TestCreateStoreFromConfig(t *testing.T) {
	// Note: This test requires a real PostgreSQL database
	// In a CI environment, this would typically be skipped or use a test database

	t.Run("Invalid config", func(t *testing.T) {
		logger := log.WithField("test", "create_store")

		// Save original environment
		originalEnv := map[string]string{
			"AUTHENTIK_POSTGRESQL__HOST": os.Getenv("AUTHENTIK_POSTGRESQL__HOST"),
			"AUTHENTIK_POSTGRESQL__USER": os.Getenv("AUTHENTIK_POSTGRESQL__USER"),
			"AUTHENTIK_POSTGRESQL__NAME": os.Getenv("AUTHENTIK_POSTGRESQL__NAME"),
		}

		// Restore environment after test
		defer func() {
			for k, v := range originalEnv {
				if v == "" {
					os.Unsetenv(k)
				} else {
					os.Setenv(k, v)
				}
			}
		}()

		// Clear required environment variables
		os.Unsetenv("AUTHENTIK_POSTGRESQL__HOST")
		os.Unsetenv("AUTHENTIK_POSTGRESQL__USER")
		os.Unsetenv("AUTHENTIK_POSTGRESQL__NAME")

		store, err := CreateStoreFromConfig("public", "test-provider", nil, logger)
		assert.Error(t, err)
		assert.Nil(t, store)
		assert.Contains(t, err.Error(), "missing fields")
	})

	t.Run("Connection failure", func(t *testing.T) {
		logger := log.WithField("test", "create_store")

		// Save original environment
		originalEnv := map[string]string{
			"AUTHENTIK_POSTGRESQL__HOST": os.Getenv("AUTHENTIK_POSTGRESQL__HOST"),
			"AUTHENTIK_POSTGRESQL__PORT": os.Getenv("AUTHENTIK_POSTGRESQL__PORT"),
			"AUTHENTIK_POSTGRESQL__USER": os.Getenv("AUTHENTIK_POSTGRESQL__USER"),
			"AUTHENTIK_POSTGRESQL__NAME": os.Getenv("AUTHENTIK_POSTGRESQL__NAME"),
		}

		// Restore environment after test
		defer func() {
			for k, v := range originalEnv {
				if v == "" {
					os.Unsetenv(k)
				} else {
					os.Setenv(k, v)
				}
			}
		}()

		// Set invalid connection parameters
		os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "nonexistent-host")
		os.Setenv("AUTHENTIK_POSTGRESQL__PORT", "5432")
		os.Setenv("AUTHENTIK_POSTGRESQL__USER", "test")
		os.Setenv("AUTHENTIK_POSTGRESQL__NAME", "test")

		store, err := CreateStoreFromConfig("public", "test-provider", nil, logger)
		assert.Error(t, err)
		assert.Nil(t, store)
	})

	t.Run("Valid config with session options", func(t *testing.T) {
		// Skip this test if no PostgreSQL connection is available
		if os.Getenv("SKIP_POSTGRES_TESTS") == "true" {
			t.Skip("Skipping PostgreSQL integration test")
		}

		logger := log.WithField("test", "create_store")

		// Save original environment
		originalEnv := map[string]string{
			"AUTHENTIK_POSTGRESQL__HOST": os.Getenv("AUTHENTIK_POSTGRESQL__HOST"),
			"AUTHENTIK_POSTGRESQL__PORT": os.Getenv("AUTHENTIK_POSTGRESQL__PORT"),
			"AUTHENTIK_POSTGRESQL__USER": os.Getenv("AUTHENTIK_POSTGRESQL__USER"),
			"AUTHENTIK_POSTGRESQL__NAME": os.Getenv("AUTHENTIK_POSTGRESQL__NAME"),
		}

		// Restore environment after test
		defer func() {
			for k, v := range originalEnv {
				if v == "" {
					os.Unsetenv(k)
				} else {
					os.Setenv(k, v)
				}
			}
		}()

		// Set test connection parameters
		os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "localhost")
		os.Setenv("AUTHENTIK_POSTGRESQL__PORT", "5432")
		os.Setenv("AUTHENTIK_POSTGRESQL__USER", "authentik")
		os.Setenv("AUTHENTIK_POSTGRESQL__NAME", "authentik_test")

		sessionOptions := &sessions.Options{
			Path:     "/test",
			MaxAge:   7200,
			HttpOnly: true,
			Secure:   true,
		}

		store, err := CreateStoreFromConfig("public", "test-provider", sessionOptions, logger)
		if err != nil {
			t.Skipf("Skipping test due to database connection error: %v", err)
		}

		require.NotNil(t, store)
		assert.NoError(t, err)

		// Verify the store was created correctly
		assert.Equal(t, "test-provider", store.ProviderID())

		// Cleanup
		store.Close()
	})
}

// Custom error types for testing
type customError struct {
	message string
}

func (e customError) Error() string {
	return e.message
}

func TestIsTableMissingError(t *testing.T) {
	t.Run("Table missing error", func(t *testing.T) {
		err := customError{message: `pq: relation "public.authentik_outposts_proxysession" does not exist`}

		result := IsTableMissingError(err)
		assert.True(t, result)
	})

	t.Run("Different table missing error", func(t *testing.T) {
		err := customError{message: `pq: relation "other_table" does not exist`}

		result := IsTableMissingError(err)
		assert.True(t, result)
	})

	t.Run("Different error", func(t *testing.T) {
		err := customError{message: "connection refused"}

		result := IsTableMissingError(err)
		assert.False(t, result)
	})

	t.Run("No error", func(t *testing.T) {
		result := IsTableMissingError(nil)
		assert.False(t, result)
	})

	t.Run("Empty error message", func(t *testing.T) {
		err := customError{message: ""}

		result := IsTableMissingError(err)
		assert.False(t, result)
	})

	t.Run("Partial match - only 'does not exist'", func(t *testing.T) {
		err := customError{message: "something does not exist"}

		result := IsTableMissingError(err)
		assert.False(t, result)
	})

	t.Run("Partial match - only 'relation'", func(t *testing.T) {
		err := customError{message: "relation has issues"}

		result := IsTableMissingError(err)
		assert.False(t, result)
	})
}

func TestPostgreSQLConnectionConfig_Edge_Cases(t *testing.T) {
	t.Run("Zero port", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     0,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=0 dbname=authentik user=authentik password=password"
		assert.Equal(t, expected, connStr)
	})

	t.Run("Negative port", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     -1,
			Database: "authentik",
			User:     "authentik",
			Password: "password",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=-1 dbname=authentik user=authentik password=password"
		assert.Equal(t, expected, connStr)
	})

	t.Run("Very long values", func(t *testing.T) {
		longString := string(make([]byte, 1000))
		for i := range longString {
			longString = longString[:i] + "a" + longString[i+1:]
		}

		config := PostgreSQLConnectionConfig{
			Host:     longString,
			Port:     5432,
			Database: longString,
			User:     longString,
			Password: longString,
		}

		connStr := config.BuildConnectionString()
		assert.Contains(t, connStr, "host="+longString)
		assert.Contains(t, connStr, "dbname="+longString)
		assert.Contains(t, connStr, "user="+longString)
		assert.Contains(t, connStr, "password="+longString)
	})

	t.Run("Unicode characters", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "authentik_测试",
			User:     "user_测试",
			Password: "pass_测试",
		}

		connStr := config.BuildConnectionString()
		expected := "host=localhost port=5432 dbname=authentik_测试 user=user_测试 password=pass_测试"
		assert.Equal(t, expected, connStr)
	})
}

func TestPostgreSQLConnectionConfig_Validation_Edge_Cases(t *testing.T) {
	logger := log.WithField("test", "validation_edge_cases")

	t.Run("All fields empty", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [host user database]")
	})

	t.Run("Only port set", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Port: 5432,
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [host user database]")
	})

	t.Run("Only SSL settings", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			SSLMode:     "require",
			SSLRootCert: "/path/to/ca.crt",
		}

		err := config.ValidateConfig(logger)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "missing fields: [host user database]")
	})

	t.Run("Whitespace values", func(t *testing.T) {
		config := PostgreSQLConnectionConfig{
			Host:     "   ",
			User:     "   ",
			Database: "   ",
			Password: "   ",
			Port:     5432, // Add port to make the test pass
		}

		// Note: The current implementation treats whitespace as non-empty
		// This test documents the current behavior
		err := config.ValidateConfig(logger)
		assert.NoError(t, err)
	})
}

// Integration tests that require a real PostgreSQL database
func TestCreateStoreFromConfig_Integration(t *testing.T) {
	// Skip integration tests by default
	if os.Getenv("RUN_INTEGRATION_TESTS") != "true" {
		t.Skip("Skipping integration test - set RUN_INTEGRATION_TESTS=true to run")
	}

	logger := log.WithField("test", "integration")

	// Save original environment
	originalEnv := map[string]string{
		"AUTHENTIK_POSTGRESQL__HOST":     os.Getenv("AUTHENTIK_POSTGRESQL__HOST"),
		"AUTHENTIK_POSTGRESQL__PORT":     os.Getenv("AUTHENTIK_POSTGRESQL__PORT"),
		"AUTHENTIK_POSTGRESQL__USER":     os.Getenv("AUTHENTIK_POSTGRESQL__USER"),
		"AUTHENTIK_POSTGRESQL__NAME":     os.Getenv("AUTHENTIK_POSTGRESQL__NAME"),
		"AUTHENTIK_POSTGRESQL__PASSWORD": os.Getenv("AUTHENTIK_POSTGRESQL__PASSWORD"),
	}

	// Restore environment after test
	defer func() {
		for k, v := range originalEnv {
			if v == "" {
				os.Unsetenv(k)
			} else {
				os.Setenv(k, v)
			}
		}
	}()

	// Set up test database connection
	os.Setenv("AUTHENTIK_POSTGRESQL__HOST", "localhost")
	os.Setenv("AUTHENTIK_POSTGRESQL__PORT", "5432")
	os.Setenv("AUTHENTIK_POSTGRESQL__USER", "authentik")
	os.Setenv("AUTHENTIK_POSTGRESQL__NAME", "authentik_test")
	os.Setenv("AUTHENTIK_POSTGRESQL__PASSWORD", "authentik")

	store, err := CreateStoreFromConfig("public", "integration-test", nil, logger)
	require.NoError(t, err)
	require.NotNil(t, store)

	// Test basic store functionality
	sqlDB, err := store.db.DB()
	assert.NoError(t, err)
	err = sqlDB.Ping()
	assert.NoError(t, err)

	// Cleanup
	err = store.Close()
	assert.NoError(t, err)
}
