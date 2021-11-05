package config

type Config struct {
	Debug          bool                 `yaml:"debug" env:"AUTHENTIK_DEBUG"`
	SecretKey      string               `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY"`
	Web            WebConfig            `yaml:"web"`
	Paths          PathsConfig          `yaml:"paths"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting"`
	Redis          RedisConfig          `yaml:"redis"`
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

type WebConfig struct {
	Listen                 string `yaml:"listen"`
	ListenTLS              string `yaml:"listen_tls"`
	ListenMetrics          string `yaml:"listen_metrics"`
	LoadLocalFiles         bool   `yaml:"load_local_files" env:"AUTHENTIK_WEB_LOAD_LOCAL_FILES"`
	DisableEmbeddedOutpost bool   `yaml:"disable_embedded_outpost" env:"AUTHENTIK_WEB__DISABLE_EMBEDDED_OUTPOST"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}

type ErrorReportingConfig struct {
	Enabled     bool   `yaml:"enabled" env:"AUTHENTIK_ERROR_REPORTING__ENABLED"`
	Environment string `yaml:"environment" env:"AUTHENTIK_ERROR_REPORTING__ENVIRONMENT"`
	SendPII     bool   `yaml:"send_pii" env:"AUTHENTIK_ERROR_REPORTING__SEND_PII"`
	DSN         string
}
