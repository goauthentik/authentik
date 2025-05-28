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
		return fmt.Sprintf("%s+%s", ver, b)
	}
	return ver
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

const VERSION = "2025.4.1"
