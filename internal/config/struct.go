package config

type Config struct {
	// Core specific config
	Storage        StorageConfig        `yaml:"storage"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL, overwrite"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting" env:", prefix=AUTHENTIK_ERROR_REPORTING__"`
	SQLite         SQLiteConfig         `yaml:"sqlite" env:", prefix=AUTHENTIK_SQLITE__"`
	Outposts       OutpostConfig        `yaml:"outposts" env:", prefix=AUTHENTIK_OUTPOSTS__"`

	// Config for core and embedded outpost
	SecretKey string `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY, overwrite"`

	// Config for both core and outposts
	Debug  bool         `yaml:"debug" env:"AUTHENTIK_DEBUG, overwrite"`
	Listen ListenConfig `yaml:"listen" env:", prefix=AUTHENTIK_LISTEN__"`
	Web    WebConfig    `yaml:"web" env:", prefix=AUTHENTIK_WEB__"`

	// Outpost specific config
	// These are only relevant for proxy/ldap outposts, and cannot be set via YAML
	// They are loaded via this config loader to support file:// schemas
	AuthentikHost        string `env:"AUTHENTIK_HOST"`
	AuthentikHostBrowser string `env:"AUTHENTIK_HOST_BROWSER"`
	AuthentikToken       string `env:"AUTHENTIK_TOKEN"`
	AuthentikInsecure    bool   `env:"AUTHENTIK_INSECURE"`
}

type SQLiteConfig struct {
	Path            string `yaml:"path" env:"PATH, overwrite"`
	CleanupInterval int    `yaml:"cleanup_interval" env:"CLEANUP_INTERVAL, overwrite"`
}

type ListenConfig struct {
	HTTP              string   `yaml:"listen_http" env:"HTTP, overwrite"`
	HTTPS             string   `yaml:"listen_https" env:"HTTPS, overwrite"`
	LDAP              string   `yaml:"listen_ldap" env:"LDAP, overwrite"`
	LDAPS             string   `yaml:"listen_ldaps" env:"LDAPS, overwrite"`
	Radius            string   `yaml:"listen_radius" env:"RADIUS, overwrite"`
	Metrics           string   `yaml:"listen_metrics" env:"METRICS, overwrite"`
	Debug             string   `yaml:"listen_debug" env:"DEBUG, overwrite"`
	TrustedProxyCIDRs []string `yaml:"trusted_proxy_cidrs" env:"TRUSTED_PROXY_CIDRS, overwrite"`
}

type StorageConfig struct {
	Media      StorageMediaConfig      `yaml:"media"`
	PostgreSQL StoragePostgreSQLConfig `yaml:"postgresql"`
}

type StorageMediaConfig struct {
	Backend string            `yaml:"backend" env:"AUTHENTIK_STORAGE__MEDIA__BACKEND"`
	File    StorageFileConfig `yaml:"file"`
}

type StorageFileConfig struct {
	Path string `yaml:"path" env:"AUTHENTIK_STORAGE__MEDIA__FILE__PATH"`
}

type StoragePostgreSQLConfig struct { // todo use prefixes like like it was done by redis
	Host        string `yaml:"host" env:"AUTHENTIK_POSTGRESQL__HOST"`
	Port        int    `yaml:"port" env:"AUTHENTIK_POSTGRESQL__PORT"`
	Name        string `yaml:"name" env:"AUTHENTIK_POSTGRESQL__NAME"`
	User        string `yaml:"user" env:"AUTHENTIK_POSTGRESQL__USER"`
	Password    string `yaml:"password" env:"AUTHENTIK_POSTGRESQL__PASSWORD"`
	SSLMode     string `yaml:"sslmode" env:"AUTHENTIK_POSTGRESQL__SSLMODE"`
	SSLRootCert string `yaml:"sslrootcert" env:"AUTHENTIK_POSTGRESQL__SSLROOTCERT"`
	SSLCert     string `yaml:"sslcert" env:"AUTHENTIK_POSTGRESQL__SSLCERT"`
	SSLKey      string `yaml:"sslkey" env:"AUTHENTIK_POSTGRESQL__SSLKEY"`
}

type ErrorReportingConfig struct {
	Enabled     bool    `yaml:"enabled" env:"ENABLED, overwrite"`
	SentryDSN   string  `yaml:"sentry_dsn" env:"SENTRY_DSN, overwrite"`
	Environment string  `yaml:"environment" env:"ENVIRONMENT, overwrite"`
	SendPII     bool    `yaml:"send_pii" env:"SEND_PII, overwrite"`
	SampleRate  float64 `yaml:"sample_rate" env:"SAMPLE_RATE, overwrite"`
}

type OutpostConfig struct {
	ContainerImageBase     string `yaml:"container_image_base" env:"CONTAINER_IMAGE_BASE, overwrite"`
	Discover               bool   `yaml:"discover" env:"DISCOVER, overwrite"`
	DisableEmbeddedOutpost bool   `yaml:"disable_embedded_outpost" env:"DISABLE_EMBEDDED_OUTPOST, overwrite"`
}

type WebConfig struct {
	Path string `yaml:"path" env:"PATH, overwrite"`
}
