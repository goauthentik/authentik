package config

import (
	"io/ioutil"

	env "github.com/Netflix/go-env"
	"github.com/imdario/mergo"
	"github.com/pkg/errors"
	log "github.com/sirupsen/logrus"
	"gopkg.in/yaml.v2"
)

var G Config

func DefaultConfig() {
	G = Config{
		Debug: false,
		Web: WebConfig{
			Listen:         "localhost:9000",
			ListenTLS:      "localhost:9443",
			LoadLocalFiles: false,
		},
		Paths: PathsConfig{
			Media: "./media",
		},
		LogLevel: "info",
		ErrorReporting: ErrorReportingConfig{
			Enabled: false,
			DSN:     "https://a579bb09306d4f8b8d8847c052d3a1d3@sentry.beryju.org/8",
		},
	}
}

func LoadConfig(path string) error {
	raw, err := ioutil.ReadFile(path)
	if err != nil {
		return errors.Wrap(err, "Failed to load config file")
	}
	nc := Config{}
	err = yaml.Unmarshal(raw, &nc)
	if err != nil {
		return errors.Wrap(err, "Failed to parse YAML")
	}
	if err := mergo.Merge(&G, nc, mergo.WithOverride); err != nil {
		return errors.Wrap(err, "failed to overlay config")
	}
	log.WithField("path", path).Debug("Loaded config")
	return nil
}

func FromEnv() error {
	nc := Config{}
	_, err := env.UnmarshalFromEnviron(&nc)
	if err != nil {
		return errors.Wrap(err, "failed to load environment variables")
	}
	if err := mergo.Merge(&G, nc, mergo.WithOverride); err != nil {
		return errors.Wrap(err, "failed to overlay config")
	}
	log.Debug("Loaded config from environment")
	return nil
}

func ConfigureLogger() {
	switch G.LogLevel {
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

	if G.Debug {
		log.SetFormatter(&log.TextFormatter{})
	} else {
		log.SetFormatter(&log.JSONFormatter{
			FieldMap: log.FieldMap{
				log.FieldKeyMsg:  "event",
				log.FieldKeyTime: "timestamp",
			},
		})
	}
}
