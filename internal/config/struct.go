package config

type Config struct {
	Debug    bool        `yaml:"debug"`
	Web      WebConfig   `yaml:"web"`
	Paths    PathsConfig `yaml:"paths"`
	LogLevel string      `yaml:"log_level"`
}

type WebConfig struct {
	Listen    string `yaml:"listen"`
	ListenTLS string `yaml:"listen_tls"`
}

type PathsConfig struct {
	Media string `yaml:"media"`
}
