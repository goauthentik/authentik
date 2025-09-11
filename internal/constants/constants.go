package constants

import (
	_ "embed"
	"fmt"
	"os"
)

//go:embed VERSION
var version string

func BUILD(def string) string {
	build := os.Getenv("GIT_BUILD_HASH")
	if build == "" {
		return def
	}
	return build
}

func VERSION() string {
	return version
}

func FullVersion() string {
	if b := BUILD(""); b != "" {
		return fmt.Sprintf("%s+%s", version, b)
	}
	return version
}

func UserAgentOutpost() string {
	return fmt.Sprintf("goauthentik.io/outpost/%s", FullVersion())
}

func UserAgentIPC() string {
	return fmt.Sprintf("goauthentik.io/ipc/%s", FullVersion())
}

func UserAgent() string {
	return fmt.Sprintf("authentik@%s", FullVersion())
}
