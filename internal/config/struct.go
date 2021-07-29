package config

type Config struct {
	Debug          bool                 `yaml:"debug" env:"AUTHENTIK_DEBUG"`
	SecretKey      string               `yaml:"secret_key" env:"AUTHENTIK_SECRET_KEY"`
	Web            WebConfig            `yaml:"web"`
	Paths          PathsConfig          `yaml:"paths"`
	LogLevel       string               `yaml:"log_level" env:"AUTHENTIK_LOG_LEVEL"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting"`
}

type WebConfig struct {
	Listen         string `yaml:"listen"`
	ListenTLS      string `yaml:"listen_tls"`
	LoadLocalFiles bool   `yaml:"load_local_files" env:"AUTHENTIK_WEB_LOAD_LOCAL_FILES"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}

type ErrorReportingConfig struct {
	Enabled     bool   `yaml:"enabled" env:"AUTHENTIK_ERROR_REPORTING__ENABLED"`
	Environment string `yaml:"environment" env:"AUTHENTIK_ERROR_REPORTING__ENVIRONMENT"`
	SendPII     bool   `yaml:"send_pii" env:"AUTHENTIK_ERROR_REPORTING__SEND_PII"`
}
