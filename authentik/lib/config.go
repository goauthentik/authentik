package lib

import _ "embed"

//go:embed default.yml
var defaultConfig []byte

func DefaultConfig() []byte {
	return defaultConfig
}
