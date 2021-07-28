package config

import (
	"os"
	"strings"
)

const ENV_PREFIX = "AUTHENTIK_"

func FromEnv() {
	for _, env := range os.Environ() {
		envPair := strings.SplitN(env, "=", 2)
		key := strings.Replace(strings.ToUpper(envPair[0]), ENV_PREFIX, "", 1)
		v := envPair[1]
		switch key {
		case "SECRET_KEY":
			G.SecretKey = v
		}
	}
}
