package config

import (
	"errors"
	"fmt"
	"net/url"
	"os"
	"reflect"
	"strings"

	env "github.com/Netflix/go-env"
	log "github.com/sirupsen/logrus"
	"gopkg.in/yaml.v2"
)

var cfg *Config

func Get() *Config {
	if cfg == nil {
		c := defaultConfig()
		c.Setup("./authentik/lib/default.yml", "/etc/authentik/config.yml", "./local.env.yml")
		cfg = c
	}
	return cfg
}

func defaultConfig() *Config {
	return &Config{
		Debug: false,
		Listen: ListenConfig{
			HTTP:    "0.0.0.0:9000",
			HTTPS:   "0.0.0.0:9443",
			LDAP:    "0.0.0.0:3389",
			LDAPS:   "0.0.0.0:6636",
			Radius:  "0.0.0.0:1812",
			Metrics: "0.0.0.0:9300",
			Debug:   "0.0.0.0:9900",
		},
		Paths: PathsConfig{
			Media: "./media",
		},
		LogLevel: "info",
		ErrorReporting: ErrorReportingConfig{
			Enabled:    false,
			SampleRate: 1,
		},
	}
}

func (c *Config) Setup(paths ...string) {
	for _, path := range paths {
		err := c.LoadConfig(path)
		if err != nil {
			log.WithError(err).Info("failed to load config, skipping")
		}
	}
	err := c.fromEnv()
	if err != nil {
		log.WithError(err).Info("failed to load env vars")
	}
	c.configureLogger()
}

func (c *Config) LoadConfig(path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return fmt.Errorf("failed to load config file: %w", err)
	}
	err = yaml.Unmarshal(raw, c)
	if err != nil {
		return fmt.Errorf("failed to parse YAML: %w", err)
	}
	c.walkScheme(c)
	log.WithField("path", path).Debug("Loaded config")
	return nil
}

func (c *Config) fromEnv() error {
	_, err := env.UnmarshalFromEnviron(c)
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
	if u.Scheme == "env" {
		e, ok := os.LookupEnv(u.Host)
		if ok {
			return e
		}
		return u.RawQuery
	} else if u.Scheme == "file" {
		d, err := os.ReadFile(u.Path)
		if err != nil {
			return u.RawQuery
		}
		return strings.TrimSpace(string(d))
	}
	return rawVal
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
