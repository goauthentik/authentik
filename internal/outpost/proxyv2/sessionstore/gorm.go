package sessionstore

import (
	"time"

	log "github.com/sirupsen/logrus"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
)

// GormConfig returns a GORM configuration with appropriate logging settings
func GormConfig(logger *log.Entry) *gorm.Config {
	// Configure GORM logger
	gormLogLevel := gormlogger.Silent
	if log.GetLevel() == log.DebugLevel {
		gormLogLevel = gormlogger.Info
	}

	gormConfig := gormlogger.Config{
		SlowThreshold:             2000, // 2 seconds
		LogLevel:                  gormLogLevel,
		IgnoreRecordNotFoundError: true,
		Colorful:                  false,
	}

	gormLogger := gormlogger.New(
		log.StandardLogger(),
		gormConfig,
	)

	return &gorm.Config{
		Logger: gormLogger,
	}
}

// ConfigureConnection sets common connection parameters for SQL database
func ConfigureConnection(sqlDB *gorm.DB) error {
	db, err := sqlDB.DB()
	if err != nil {
		return err
	}

	// Set connection parameters
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)

	return nil
}

// MigrateSchema runs auto-migration for the ProxySession model
func MigrateSchema(db *gorm.DB, schema string) error {
	// For outposts, we only need to handle SQLite migrations
	// The PostgreSQL migrations are managed by Django in authentik/outposts/models.py

	// Run auto-migration for SQLite
	if err := db.AutoMigrate(&ProxySession{}); err != nil {
		return err
	}

	// Create a composite unique index for session_key and provider_id
	indexName := "idx_session_key_provider_id"
	migrator := db.Migrator()

	if !migrator.HasIndex(&ProxySession{}, indexName) {
		if err := migrator.CreateIndex(&ProxySession{}, indexName); err != nil {
			return err
		}
	}

	return nil
}
