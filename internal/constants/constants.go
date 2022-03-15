package constants

import (
	"fmt"
	"os"
)

func BUILD(def string) string {
	build := os.Getenv("GIT_BUILD_HASH")
	if build == "" {
		return def
	}
	return build
}

func FullVersion() string {
	ver := VERSION
	if b := BUILD(""); b != "" {
		ver = fmt.Sprintf("%s.%s", ver, b)
	}
	return ver
}

func OutpostUserAgent() string {
	return fmt.Sprintf("authentik-outpost@%s", FullVersion())
}

const VERSION = "2022.3.2"
