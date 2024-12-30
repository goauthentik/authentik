package config

import (
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
	return log.WithOptions(zap.Hooks(func(e zapcore.Entry) error {
		return nil
	}))
}

func Trace() zap.Field {
	return zap.Skip()
}
