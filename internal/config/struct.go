package config

type Config struct {
	// Core specific config
	Storage        StorageConfig        `yaml:"storage"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL, overwrite"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting" env:", prefix=AUTHENTIK_ERROR_REPORTING__"`
	PostgreSQL     PostgreSQLConfig     `yaml:"postgresql" env:", prefix=AUTHENTIK_POSTGRESQL__"`
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

type PostgreSQLConfig struct {
	Host     string `yaml:"host" env:"HOST, overwrite"`
	Port     int    `yaml:"port" env:"PORT, overwrite"`
	User     string `yaml:"user" env:"USER, overwrite"`
	Password string `yaml:"password" env:"PASSWORD, overwrite"`
	Name     string `yaml:"name" env:"NAME, overwrite"`

	// SSL/TLS settings
	SSLMode     string `yaml:"sslmode" env:"SSLMODE, overwrite"`
	SSLRootCert string `yaml:"sslrootcert" env:"SSLROOTCERT, overwrite"`
	SSLCert     string `yaml:"sslcert" env:"SSLCERT, overwrite"`
	SSLKey      string `yaml:"sslkey" env:"SSLKEY, overwrite"`

	// Connection management
	ConnMaxAge               int  `yaml:"conn_max_age" env:"CONN_MAX_AGE, overwrite"`
	ConnHealthChecks         bool `yaml:"conn_health_checks" env:"CONN_HEALTH_CHECKS, overwrite"`
	DisableServerSideCursors bool `yaml:"disable_server_side_cursors" env:"DISABLE_SERVER_SIDE_CURSORS, overwrite"`

	// Advanced settings
	DefaultSchema string `yaml:"default_schema" env:"DEFAULT_SCHEMA, overwrite"`
	ConnOptions   string `yaml:"conn_options" env:"CONN_OPTIONS, overwrite"`
}

type ListenConfig struct {
	HTTP              string   `yaml:"http" env:"HTTP, overwrite"`
	HTTPS             string   `yaml:"https" env:"HTTPS, overwrite"`
	LDAP              string   `yaml:"ldap" env:"LDAP, overwrite"`
	LDAPS             string   `yaml:"ldaps" env:"LDAPS, overwrite"`
	Radius            string   `yaml:"radius" env:"RADIUS, overwrite"`
	Metrics           string   `yaml:"metrics" env:"METRICS, overwrite"`
	Debug             string   `yaml:"debug" env:"DEBUG, overwrite"`
	TrustedProxyCIDRs []string `yaml:"trusted_proxy_cidrs" env:"TRUSTED_PROXY_CIDRS, overwrite"`
}

type StorageConfig struct {
	Media StorageMediaConfig `yaml:"media"`
}

type StorageMediaConfig struct {
	Backend string            `yaml:"backend" env:"AUTHENTIK_STORAGE__MEDIA__BACKEND"`
	File    StorageFileConfig `yaml:"file"`
}

type StorageFileConfig struct {
	Path string `yaml:"path" env:"AUTHENTIK_STORAGE__MEDIA__FILE__PATH"`
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
