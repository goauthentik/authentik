package config

import "time"

type Config struct {
	LogLevel string `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL, overwrite"`

	// Config for both core and outposts
	Debug  bool         `yaml:"debug" env:"AUTHENTIK_DEBUG, overwrite"`
	Listen ListenConfig `yaml:"listen" env:", prefix=AUTHENTIK_LISTEN__"`
	Log    LogConfig    `yaml:"log" env:", prefix=AUTHENTIK_LOG__"`
	LDAP   LDAPConfig   `yaml:"ldap" env:", prefix=AUTHENTIK_LDAP__"`

	// Outpost specific config
	// These are only relevant for proxy/ldap outposts, and cannot be set via YAML
	// They are loaded via this config loader to support file:// schemas
	AuthentikHost                string        `env:"AUTHENTIK_HOST"`
	AuthentikHostBrowser         string        `env:"AUTHENTIK_HOST_BROWSER"`
	AuthentikToken               string        `env:"AUTHENTIK_TOKEN"`
	AuthentikInsecure            bool          `env:"AUTHENTIK_INSECURE"`
	AuthentikCertificateCacheTTL time.Duration `env:"AUTHENTIK_CERT_CACHE_TTL"`
}

type ListenConfig struct {
	LDAP              []string `yaml:"ldap" env:"LDAP, overwrite"`
	LDAPS             []string `yaml:"ldaps" env:"LDAPS, overwrite"`
	Radius            []string `yaml:"radius" env:"RADIUS, overwrite"`
	Metrics           []string `yaml:"metrics" env:"METRICS, overwrite"`
	Debug             string   `yaml:"debug" env:"DEBUG, overwrite"`
	TrustedProxyCIDRs []string `yaml:"trusted_proxy_cidrs" env:"TRUSTED_PROXY_CIDRS, overwrite"`
}

type LogConfig struct {
	HttpHeaders []string `yaml:"http_headers" env:"HTTP_HEADERS, overwrite"`
}

type LDAPConfig struct {
	PageSize int `yaml:"page_size" env:"PAGE_SIZE, overwrite"`
}
