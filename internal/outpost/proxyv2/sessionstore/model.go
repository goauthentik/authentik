package sessionstore

import (
	"time"
)

// ProxySession is the GORM model for storing proxy sessions
// This matches the Django model in authentik/outposts/models.py
type ProxySession struct {
	UUID       string     `gorm:"primaryKey;type:varchar(36);column:uuid"`
	ProviderID string     `gorm:"type:varchar(255);uniqueIndex:idx_session_key_provider_id;column:provider_id"`
	SessionKey string     `gorm:"type:varchar(255);uniqueIndex:idx_session_key_provider_id;column:session_key"`
	Data       []byte     `gorm:"type:bytea;column:data"`
	Claims     string     `gorm:"type:text;column:claims"`
	Redirect   string     `gorm:"type:text;column:redirect"`
	CreatedAt  time.Time  `gorm:"autoCreateTime;column:created_at"`
	UpdatedAt  time.Time  `gorm:"autoUpdateTime;column:updated_at"`
	DeletedAt  *time.Time `gorm:"index;column:deleted_at"`
	// From ExpiringModel
	Expires  *time.Time `gorm:"index;column:expires"`
	Expiring bool       `gorm:"default:true;column:expiring"`
}

// TableName overrides the table name used by GORM
func (ProxySession) TableName() string {
	return "authentik_outposts_proxysession"
}
