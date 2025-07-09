package pgstore

import (
	"fmt"
	"strings"

	"github.com/gorilla/sessions"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

// PostgreSQLConnectionConfig holds connection configuration for PostgreSQL
type PostgreSQLConnectionConfig struct {
	Host        string
	Port        int
	Database    string
	User        string
	Password    string
	SSLMode     string
	SSLRootCert string
	SSLCert     string
	SSLKey      string
}

// LoadPostgreSQLConfig loads PostgreSQL configuration from the global config
func LoadPostgreSQLConfig() PostgreSQLConnectionConfig {
	pgConfig := config.Get().PostgreSQL

	return PostgreSQLConnectionConfig{
		Host:        pgConfig.Host,
		Port:        int(pgConfig.Port),
		Database:    pgConfig.Name,
		User:        pgConfig.User,
		Password:    pgConfig.Password,
		SSLMode:     pgConfig.SSLMode,
		SSLRootCert: pgConfig.SSLRootCert,
		SSLCert:     pgConfig.SSLCert,
		SSLKey:      pgConfig.SSLKey,
	}
}

// ValidateConfig validates the PostgreSQL configuration for embedded outposts
func (c PostgreSQLConnectionConfig) ValidateConfig(logger *log.Entry) error {
	logger.WithFields(log.Fields{
		"host":       c.Host,
		"port":       c.Port,
		"database":   c.Database,
		"user":       c.User,
		"sslmode":    c.SSLMode,
		"has_cert":   c.SSLCert != "",
		"has_key":    c.SSLKey != "",
		"has_rootca": c.SSLRootCert != "",
	}).Debug("Loaded PostgreSQL configuration for embedded outpost")

	// Collect missing required fields
	missingFields := []string{}
	missingEnvVars := []string{}

	if c.Host == "" {
		missingFields = append(missingFields, "host")
		missingEnvVars = append(missingEnvVars, "AUTHENTIK_POSTGRESQL__HOST")
	}

	if c.User == "" {
		missingFields = append(missingFields, "user")
		missingEnvVars = append(missingEnvVars, "AUTHENTIK_POSTGRESQL__USER")
	}

	if c.Database == "" {
		missingFields = append(missingFields, "database")
		missingEnvVars = append(missingEnvVars, "AUTHENTIK_POSTGRESQL__NAME")
	}

	if c.Password == "" {
		logger.Warning("PostgreSQL password is empty - check AUTHENTIK_POSTGRESQL__PASSWORD environment variable")
	}

	if len(missingFields) > 0 {
		logger.WithFields(log.Fields{
			"missing_fields":   missingFields,
			"missing_env_vars": missingEnvVars,
		}).Error("PostgreSQL connection not properly configured for embedded outpost - check environment variables")

		return fmt.Errorf("PostgreSQL connection not properly configured for embedded outpost - missing fields: %v (set env vars: %v)", missingFields, missingEnvVars)
	}

	return nil
}

// BuildConnectionString builds a PostgreSQL connection string from the configuration
func (c PostgreSQLConnectionConfig) BuildConnectionString() string {
	connStr := fmt.Sprintf("host=%s port=%d dbname=%s user=%s password=%s",
		c.Host, c.Port, c.Database, c.User, c.Password)

	if c.SSLMode != "" {
		connStr += fmt.Sprintf(" sslmode=%s", c.SSLMode)
	}
	if c.SSLRootCert != "" {
		connStr += fmt.Sprintf(" sslrootcert=%s", c.SSLRootCert)
	}
	if c.SSLCert != "" {
		connStr += fmt.Sprintf(" sslcert=%s", c.SSLCert)
	}
	if c.SSLKey != "" {
		connStr += fmt.Sprintf(" sslkey=%s", c.SSLKey)
	}

	return connStr
}

// CreateStoreFromConfig creates a new PostgreSQL store with validation
func CreateStoreFromConfig(schema string, providerID string, sessionOptions *sessions.Options, logger *log.Entry) (*PGStore, error) {
	config := LoadPostgreSQLConfig()

	if err := config.ValidateConfig(logger); err != nil {
		return nil, err
	}

	connStr := config.BuildConnectionString()

	// Log connection attempt
	logger.WithFields(log.Fields{
		"host":     config.Host,
		"port":     config.Port,
		"database": config.Database,
		"user":     config.User,
		"schema":   schema,
		"sslmode":  config.SSLMode,
		"has_cert": config.SSLCert != "",
	}).Debug("Connecting to PostgreSQL")

	return NewPGStore(connStr, schema, providerID, sessionOptions)
}

// IsTableMissingError checks if an error is due to missing PostgreSQL table
func IsTableMissingError(err error) bool {
	if err == nil {
		return false
	}
	return strings.Contains(err.Error(), "does not exist") && strings.Contains(err.Error(), "relation")
}
