package config

type Config struct {
	Debug bool
	Web   WebConfig
	Paths PathsConfig
	Log   LogConfig
}

type WebConfig struct {
	Listen    string
	ListenTLS string
}

type PathsConfig struct {
	Media string
}

type LogConfig struct {
	Level  string
	Format string
}
