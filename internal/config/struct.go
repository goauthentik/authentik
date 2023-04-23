package config

type Config struct {
	// Core specific config
	Paths          PathsConfig          `yaml:"paths"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting"`
	Redis          RedisConfig          `yaml:"redis"`
	Outposts       OutpostConfig        `yaml:"outposts"`

	// Config for core and embedded outpost
	SecretKey string `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY"`

	// Config for both core and outposts
	Debug  bool         `yaml:"debug" env:"AUTHENTIK_DEBUG"`
	Listen ListenConfig `yaml:"listen"`

	// Outpost specific config
	// These are only relevant for proxy/ldap outposts, and cannot be set via YAML
	// They are loaded via this config loader to support file:// schemas
	AuthentikHost        string `env:"AUTHENTIK_HOST"`
	AuthentikHostBrowser string `env:"AUTHENTIK_HOST_BROWSER"`
	AuthentikToken       string `env:"AUTHENTIK_TOKEN"`
	AuthentikInsecure    bool   `env:"AUTHENTIK_INSECURE"`
}

type RedisConfig struct {
	Host                   string `yaml:"host" env:"AUTHENTIK_REDIS__HOST"`
	Port                   int    `yaml:"port" env:"AUTHENTIK_REDIS__PORT"`
	Password               string `yaml:"password" env:"AUTHENTIK_REDIS__PASSWORD"`
	TLS                    bool   `yaml:"tls" env:"AUTHENTIK_REDIS__TLS"`
	TLSReqs                string `yaml:"tls_reqs" env:"AUTHENTIK_REDIS__TLS_REQS"`
	DB                     int    `yaml:"cache_db" env:"AUTHENTIK_REDIS__DB"`
	CacheTimeout           int    `yaml:"cache_timeout" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT"`
	CacheTimeoutFlows      int    `yaml:"cache_timeout_flows" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_FLOWS"`
	CacheTimeoutPolicies   int    `yaml:"cache_timeout_policies" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_POLICIES"`
	CacheTimeoutReputation int    `yaml:"cache_timeout_reputation" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_REPUTATION"`
}

type ListenConfig struct {
	HTTP    string `yaml:"listen_http" env:"AUTHENTIK_LISTEN__HTTP"`
	HTTPS   string `yaml:"listen_https" env:"AUTHENTIK_LISTEN__HTTPS"`
	LDAP    string `yaml:"listen_ldap" env:"AUTHENTIK_LISTEN__LDAP"`
	LDAPS   string `yaml:"listen_ldaps" env:"AUTHENTIK_LISTEN__LDAPS"`
	Radius  string `yaml:"listen_radius" env:"AUTHENTIK_LISTEN__RADIUS"`
	Metrics string `yaml:"listen_metrics" env:"AUTHENTIK_LISTEN__METRICS"`
	Debug   string `yaml:"listen_debug" env:"AUTHENTIK_LISTEN__DEBUG"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}

type ErrorReportingConfig struct {
	Enabled     bool    `yaml:"enabled" env:"AUTHENTIK_ERROR_REPORTING__ENABLED"`
	SentryDSN   string  `yaml:"sentry_dsn" env:"AUTHENTIK_ERROR_REPORTING__SENTRY_DSN"`
	Environment string  `yaml:"environment" env:"AUTHENTIK_ERROR_REPORTING__ENVIRONMENT"`
	SendPII     bool    `yaml:"send_pii" env:"AUTHENTIK_ERROR_REPORTING__SEND_PII"`
	SampleRate  float64 `yaml:"sample_rate" env:"AUTHENTIK_ERROR_REPORTING__SAMPLE_RATE"`
}

type OutpostConfig struct {
	ContainerImageBase     string `yaml:"container_image_base" env:"AUTHENTIK_OUTPOSTS__CONTAINER_IMAGE_BASE"`
	Discover               bool   `yaml:"discover" env:"AUTHENTIK_OUTPOSTS__DISCOVER"`
	DisableEmbeddedOutpost bool   `yaml:"disable_embedded_outpost" env:"AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST"`
}
