package config

import (
	"context"
	_ "embed"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"strings"

	env "github.com/sethvargo/go-envconfig"
	log "github.com/sirupsen/logrus"
	"gopkg.in/yaml.v2"

	"goauthentik.io/authentik/lib"
)

var cfg *Config

const defaultConfigPath = "./authentik/lib/default.yml"

func getConfigPaths() []string {
	configPaths := []string{defaultConfigPath, "/etc/authentik/config.yml", ""}
	if workspace := os.Getenv("WORKSPACE_DIR"); workspace != "" {
		_ = os.Chdir(workspace)
	}
	globConfigPaths, _ := filepath.Glob("/etc/authentik/config.d/*.yml")
	configPaths = append(configPaths, globConfigPaths...)

	environment := "local"
	if v, ok := os.LookupEnv("AUTHENTIK_ENV"); ok {
		environment = v
	}

	computedConfigPaths := []string{}

	for _, path := range configPaths {
		path, err := filepath.Abs(path)
		if err != nil {
			continue
		}
		if stat, err := os.Stat(path); err == nil {
			if !stat.IsDir() {
				computedConfigPaths = append(computedConfigPaths, path)
			} else {
				envPaths := []string{
					filepath.Join(path, environment+".yml"),
					filepath.Join(path, environment+".env.yml"),
				}
				for _, envPath := range envPaths {
					if stat, err = os.Stat(envPath); err == nil && !stat.IsDir() {
						computedConfigPaths = append(computedConfigPaths, envPath)
					}
				}
			}
		}
	}

	return computedConfigPaths
}

func Get() *Config {
	if cfg == nil {
		c := &Config{}
		c.Setup(getConfigPaths()...)
		cfg = c
	}
	return cfg
}

func (c *Config) Setup(paths ...string) {
	// initially try to load the default config which is compiled in
	err := c.LoadConfig(lib.DefaultConfig())
	// this should never fail
	if err != nil {
		panic(fmt.Errorf("failed to load inbuilt config: %v", err))
	}
	log.WithField("path", "inbuilt-default").Debug("Loaded config")
	for _, path := range paths {
		err := c.LoadConfigFromFile(path)
		if err != nil {
			log.WithError(err).Info("failed to load config, skipping")
		}
	}
	err = c.fromEnv()
	if err != nil {
		log.WithError(err).Info("failed to load env vars")
	}
	c.configureLogger()
}

func (c *Config) LoadConfig(raw []byte) error {
	err := yaml.Unmarshal(raw, c)
	if err != nil {
		return fmt.Errorf("failed to parse YAML: %w", err)
	}
	c.walkScheme(c)
	return nil
}

func (c *Config) LoadConfigFromFile(path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return fmt.Errorf("failed to load config file: %w", err)
	}
	err = c.LoadConfig(raw)
	if err != nil {
		return err
	}
	log.WithField("path", path).Debug("Loaded config")
	return nil
}

func (c *Config) fromEnv() error {
	ctx := context.Background()
	err := env.Process(ctx, c)
	if err != nil {
		return fmt.Errorf("failed to load environment variables: %w", err)
	}
	c.walkScheme(c)
	log.Debug("Loaded config from environment")
	return nil
}

func (c *Config) walkScheme(v interface{}) {
	rv := reflect.ValueOf(v)
	if rv.Kind() != reflect.Ptr || rv.IsNil() {
		return
	}

	rv = rv.Elem()
	if rv.Kind() != reflect.Struct {
		return
	}

	t := rv.Type()
	for i := 0; i < rv.NumField(); i++ {
		valueField := rv.Field(i)
		switch valueField.Kind() {
		case reflect.Struct:
			if !valueField.Addr().CanInterface() {
				continue
			}

			iface := valueField.Addr().Interface()
			c.walkScheme(iface)
		}

		typeField := t.Field(i)
		if typeField.Type.Kind() != reflect.String {
			continue
		}
		valueField.SetString(c.parseScheme(valueField.String()))
	}
}

func (c *Config) parseScheme(rawVal string) string {
	u, err := url.Parse(rawVal)
	if err != nil {
		return rawVal
	}
	switch u.Scheme {
	case "env":
		e, ok := os.LookupEnv(u.Host)
		if ok {
			log.WithFields(log.Fields{
				"env_var": u.Host,
				"found":   true,
			}).Trace("Resolved environment variable")
			return e
		}
		log.WithFields(log.Fields{
			"env_var":  u.Host,
			"found":    false,
			"fallback": u.RawQuery,
		}).Warn("Environment variable not found, using fallback")
		return u.RawQuery
	case "file":
		d, err := os.ReadFile(u.Path)
		if err != nil {
			return u.RawQuery
		}
		return strings.TrimSpace(string(d))
	}
	return rawVal
}

// RefreshPostgreSQLConfig re-reads PostgreSQL configuration from file:// and env:// URIs
// This enables hot-reloading when credentials are rotated by updating the referenced files.
// Note: Plain environment variables (without file:// or env:// prefixes) are read from the
// process environment and will not change unless the process is restarted or os.Setenv is called.
func (c *Config) RefreshPostgreSQLConfig() PostgreSQLConfig {
	// Start with current config as base
	refreshed := c.PostgreSQL

	// Manually read from environment variables with proper prefix
	// We can't use env.Process directly on PostgreSQLConfig because it loses the AUTHENTIK_POSTGRESQL__ prefix
	// Map of environment variable suffix to config field pointer
	envVars := map[string]*string{
		"HOST":           &refreshed.Host,
		"PORT":           &refreshed.Port,
		"USER":           &refreshed.User,
		"PASSWORD":       &refreshed.Password,
		"NAME":           &refreshed.Name,
		"SSLMODE":        &refreshed.SSLMode,
		"SSLROOTCERT":    &refreshed.SSLRootCert,
		"SSLCERT":        &refreshed.SSLCert,
		"SSLKEY":         &refreshed.SSLKey,
		"DEFAULT_SCHEMA": &refreshed.DefaultSchema,
		"CONN_OPTIONS":   &refreshed.ConnOptions,
	}

	// Read each environment variable if it exists
	for suffix, field := range envVars {
		if val, ok := os.LookupEnv("AUTHENTIK_POSTGRESQL__" + suffix); ok {
			*field = val
		}
	}

	// Process file:// and env:// URI schemes
	c.walkScheme(&refreshed)

	return refreshed
}

func (c *Config) configureLogger() {
	switch strings.ToLower(c.LogLevel) {
	case "trace":
		log.SetLevel(log.TraceLevel)
	case "debug":
		log.SetLevel(log.DebugLevel)
	case "info":
		log.SetLevel(log.InfoLevel)
	case "warning":
		log.SetLevel(log.WarnLevel)
	case "error":
		log.SetLevel(log.ErrorLevel)
	default:
		log.SetLevel(log.DebugLevel)
	}

	fm := log.FieldMap{
		log.FieldKeyMsg:  "event",
		log.FieldKeyTime: "timestamp",
	}

	if c.Debug {
		log.SetFormatter(&log.TextFormatter{FieldMap: fm})
	} else {
		log.SetFormatter(&log.JSONFormatter{FieldMap: fm, DisableHTMLEscape: true})
	}
}
