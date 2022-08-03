package config

type Config struct {
	Debug                  bool                 `yaml:"debug" env:"AUTHENTIK_DEBUG"`
	SecretKey              string               `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY"`
	Listen                 ListenConfig         `yaml:"listen"`
	Paths                  PathsConfig          `yaml:"paths"`
	LogLevel               string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL"`
	ErrorReporting         ErrorReportingConfig `yaml:"error_reporting"`
	Redis                  RedisConfig          `yaml:"redis"`
	DisableEmbeddedOutpost bool                 `yaml:"disable_embedded_outpost" env:"AUTHENTIK_WEB__DISABLE_EMBEDDED_OUTPOST"`
}

type RedisConfig struct {
	Host                   string `yaml:"host" env:"AUTHENTIK_REDIS__HOST"`
	Port                   int    `yaml:"port" env:"AUTHENTIK_REDIS__PORT"`
	Password               string `yaml:"password" env:"AUTHENTIK_REDIS__PASSWORD"`
	TLS                    bool   `yaml:"tls" env:"AUTHENTIK_REDIS__TLS"`
	TLSReqs                string `yaml:"tls_reqs" env:"AUTHENTIK_REDIS__TLS_REQS"`
	CacheDB                int    `yaml:"cache_db" env:"AUTHENTIK_REDIS__CACHE_DB"`
	MessageQueueDB         int    `yaml:"message_queue_db" env:"AUTHENTIK_REDIS__MESSAGE_QUEUE_DB"`
	WSDB                   int    `yaml:"ws_db" env:"AUTHENTIK_REDIS__WS_DB"`
	OutpostSessionDB       int    `yaml:"outpost_session_db" env:"AUTHENTIK_REDIS__OUTPOST_SESSION_DB"`
	CacheTimeout           int    `yaml:"cache_timeout" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT"`
	CacheTimeoutFlows      int    `yaml:"cache_timeout_flows" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_FLOWS"`
	CacheTimeoutPolicies   int    `yaml:"cache_timeout_policies" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_POLICIES"`
	CacheTimeoutReputation int    `yaml:"cache_timeout_reputation" env:"AUTHENTIK_REDIS__CACHE_TIMEOUT_REPUTATION"`
}

type ListenConfig struct {
	HTTP    string `yaml:"listen_http" env:"AUTHENTIK_LISTEN__HTTP"`
	HTTPS   string `yaml:"listen_https" env:"AUTHENTIK_LISTEN__HTTPS"`
	LDAP    string `yaml:"listen_ldap" env:"AUTHENTIK_LISTEN__LDAP,default=0.0.0.0:3389"`
	LDAPS   string `yaml:"listen_ldaps" env:"AUTHENTIK_LISTEN__LDAPS,default=0.0.0.0:6636"`
	Metrics string `yaml:"listen_metrics" env:"AUTHENTIK_LISTEN__LISTEN_METRICS,default=0.0.0.0:9300"`
	Debug   string `yaml:"listen_debug" env:"AUTHENTIK_LISTEN__LISTEN_DEBUG,default=0.0.0.0:9900"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}

type ErrorReportingConfig struct {
	Enabled     bool   `yaml:"enabled" env:"AUTHENTIK_ERROR_REPORTING__ENABLED"`
	Environment string `yaml:"environment" env:"AUTHENTIK_ERROR_REPORTING__ENVIRONMENT"`
	SendPII     bool   `yaml:"send_pii" env:"AUTHENTIK_ERROR_REPORTING__SEND_PII"`
	DSN         string
	SampleRate  float64 `yaml:"sample_rate" env:"AUTHENTIK_ERROR_REPORTING__SAMPLE_RATE"`
}
