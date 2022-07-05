package config

import (
	"fmt"
	"io/ioutil"
	"strings"

	env "github.com/Netflix/go-env"
	"github.com/imdario/mergo"
	log "github.com/sirupsen/logrus"
	"gopkg.in/yaml.v2"
)

var G Config

func DefaultConfig() {
	G = Config{
		Debug: false,
		Web: WebConfig{
			Listen:    "localhost:9000",
			ListenTLS: "localhost:9443",
		},
		Paths: PathsConfig{
			Media: "./media",
		},
		LogLevel: "info",
		ErrorReporting: ErrorReportingConfig{
			Enabled:    false,
			DSN:        "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
			SampleRate: 1,
		},
	}
}

func LoadConfig(path string) error {
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		return fmt.Errorf("Failed to load config file: %w", err)
	}
	nc := Config{}
	err = yaml.Unmarshal(raw, &nc)
	if err != nil {
		return fmt.Errorf("Failed to parse YAML: %w", err)
	}
	if err := mergo.Merge(&G, nc, mergo.WithOverride); err != nil {
		return fmt.Errorf("failed to overlay config: %w", err)
	}
	log.WithField("path", path).Debug("Loaded config")
	return nil
}

func FromEnv() error {
	nc := Config{}
	_, err := env.UnmarshalFromEnviron(&nc)
	if err != nil {
		return fmt.Errorf("failed to load environment variables: %w", err)
	}
	if err := mergo.Merge(&G, nc, mergo.WithOverride); err != nil {
		return fmt.Errorf("failed to overlay config: %w", err)
	}
	log.Debug("Loaded config from environment")
	return nil
}

func ConfigureLogger() {
	switch strings.ToLower(G.LogLevel) {
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

	if G.Debug {
		log.SetFormatter(&log.TextFormatter{FieldMap: fm})
	} else {
		log.SetFormatter(&log.JSONFormatter{FieldMap: fm, DisableHTMLEscape: true})
	}
}
