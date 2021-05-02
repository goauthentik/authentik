package config

import (
	log "github.com/sirupsen/logrus"
)

var G Config

func DefaultConfig() {
	G = Config{
		Debug: true,
		Web: WebConfig{
			Listen:    "localhost:9000",
			ListenTLS: "localhost:9443",
		},
		Paths: PathsConfig{
			Media: "./media",
		},
		Log: LogConfig{
			Level:  "trace",
			Format: "json",
		},
	}
}

func ConfigureLogger() {
	switch G.Log.Level {
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

	switch G.Log.Format {
	case "json":
		log.SetFormatter(&log.JSONFormatter{
			FieldMap: log.FieldMap{
				log.FieldKeyMsg:  "event",
				log.FieldKeyTime: "timestamp",
			},
		})
	default:
		log.SetFormatter(&log.TextFormatter{})
	}
}
