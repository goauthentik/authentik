package config

type Config struct {
	Debug          bool                 `yaml:"debug"`
	SecretKey      string               `yaml:"secret_key"`
	Web            WebConfig            `yaml:"web"`
	Paths          PathsConfig          `yaml:"paths"`
	LogLevel       string               `yaml:"log_level"`
	ErrorReporting ErrorReportingConfig `yaml:"error_reporting"`
}

type WebConfig struct {
	Listen         string `yaml:"listen"`
	ListenTLS      string `yaml:"listen_tls"`
	LoadLocalFiles bool   `yaml:"load_local_files"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}

type ErrorReportingConfig struct {
	Enabled     bool   `yaml:"enabled"`
	Environment string `yaml:"environment"`
	SendPII     bool   `yaml:"send_pii"`
}
