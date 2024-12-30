package config

import (
	"strings"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"goauthentik.io/internal/constants"
)

func (c *Config) Logger() *zap.Logger {
	return c.log
}

func (c *Config) SetLogger(l *zap.Logger) {
	c.log = l
}

func (c *Config) BuildLogger() *zap.Logger {
	l, err := zapcore.ParseLevel(c.LogLevel)
	if err != nil {
		l = zapcore.InfoLevel
	}
	if c.Debug {
		l = zapcore.DebugLevel
	}
	return c.BuildLoggerWithLevel(l)
}

type TraceFilterCore struct {
	zapcore.Core
}

func (c *TraceFilterCore) isTrace(fields []zapcore.Field) bool {
	for _, f := range fields {
		if _, ok := f.Interface.(trace); ok {
			return true
		}
	}
	return false
}

func (c *TraceFilterCore) Check(entry zapcore.Entry, checked *zapcore.CheckedEntry) *zapcore.CheckedEntry {
	if c.Enabled(entry.Level) {
		return checked.AddCore(entry, c)
	}
	return checked
}

func (c *TraceFilterCore) Write(entry zapcore.Entry, fields []zapcore.Field) error {
	if c.isTrace(fields) {
		if !strings.EqualFold(Get().LogLevel, "trace") {
			return nil
		}
	}
	return c.Core.Write(entry, fields)
}

func (c *Config) BuildLoggerWithLevel(l zapcore.Level) *zap.Logger {
	enc := zap.NewProductionEncoderConfig()
	enc.MessageKey = "event"
	enc.TimeKey = "timestamp"
	config := zap.Config{
		Encoding:         "json",
		Development:      false,
		OutputPaths:      []string{"stdout"},
		ErrorOutputPaths: []string{"stderr"},
		EncoderConfig:    enc,
	}
	config.Level = zap.NewAtomicLevelAt(l)
	config.DisableCaller = !c.Debug
	if c.Debug {
		config.Development = false
		config.Encoding = "console"
		config.EncoderConfig = zap.NewDevelopmentEncoderConfig()
		config.EncoderConfig.MessageKey = "event"
		config.EncoderConfig.TimeKey = "timestamp"
		config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	}
	if constants.CI() {
		config.EncoderConfig.EncodeLevel = zapcore.CapitalLevelEncoder
	}
	config.EncoderConfig.EncodeDuration = zapcore.MillisDurationEncoder
	log, err := config.Build()
	if err != nil {
		panic(err)
	}
	return zap.New(&TraceFilterCore{log.Core()})
}

type trace struct{}

func Trace() zap.Field {
	return zap.Field{
		Type:      zapcore.SkipType,
		Interface: trace{},
	}
}
