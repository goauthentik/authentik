package postgresstore

import (
	"context"
	"time"

	log "github.com/sirupsen/logrus"
	gormlogger "gorm.io/gorm/logger"
)

type logrusLogger struct {
	logger *log.Entry
}

func NewLogger(parent *log.Entry) *logrusLogger {
	return &logrusLogger{
		logger: parent,
	}
}

func (l *logrusLogger) LogMode(gormlogger.LogLevel) gormlogger.Interface {
	return l
}

func (l *logrusLogger) Info(ctx context.Context, s string, args ...interface{}) {
	l.logger.WithContext(ctx).Infof(s, args...)
}

func (l *logrusLogger) Warn(ctx context.Context, s string, args ...interface{}) {
	l.logger.WithContext(ctx).Warnf(s, args...)
}

func (l *logrusLogger) Error(ctx context.Context, s string, args ...interface{}) {
	l.logger.WithContext(ctx).Errorf(s, args...)
}

func (l *logrusLogger) Trace(ctx context.Context, begin time.Time, fc func() (string, int64), err error) {
	elapsed := time.Since(begin)
	sql, _ := fc()
	fields := log.Fields{
		"elapsed": elapsed,
	}
	if err != nil {
		l.logger.WithContext(ctx).WithFields(fields).WithError(err).Error(sql)
		return
	}
	l.logger.WithContext(ctx).WithFields(fields).Trace(sql)
}
