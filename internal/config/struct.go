package config

type Config struct {
	// Core specific config
	Paths          PathsConfig          `yaml:"paths"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL, overwrite"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting" env:", prefix=AUTHENTIK_ERROR_REPORTING__"`
	Redis          RedisConfig          `yaml:"redis" env:", prefix=AUTHENTIK_REDIS__"`
	Outposts       OutpostConfig        `yaml:"outposts" env:", prefix=AUTHENTIK_OUTPOSTS__"`

	// Config for core and embedded outpost
	SecretKey string `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY, overwrite"`

	// Config for both core and outposts
	Debug  bool         `yaml:"debug" env:"AUTHENTIK_DEBUG, overwrite"`
	Listen ListenConfig `yaml:"listen" env:", prefix=AUTHENTIK_LISTEN__"`

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
	HTTP              string   `yaml:"listen_http" env:"HTTP, overwrite"`
	HTTPS             string   `yaml:"listen_https" env:"HTTPS, overwrite"`
	LDAP              string   `yaml:"listen_ldap" env:"LDAP, overwrite"`
	LDAPS             string   `yaml:"listen_ldaps" env:"LDAPS, overwrite"`
	Radius            string   `yaml:"listen_radius" env:"RADIUS, overwrite"`
	Metrics           string   `yaml:"listen_metrics" env:"METRICS, overwrite"`
	Debug             string   `yaml:"listen_debug" env:"DEBUG, overwrite"`
	TrustedProxyCIDRs []string `yaml:"trusted_proxy_cidrs" env:"TRUSTED_PROXY_CIDRS, overwrite"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
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
