package constants

import (
	"fmt"
	"os"
)

func BUILD() string {
	build := os.Getenv("GIT_BUILD_HASH")
	if build == "" {
		return "tagged"
	}
	return build
}

func OutpostUserAgent() string {
	return fmt.Sprintf("authentik-outpost@%s (%s)", VERSION, BUILD())
}

const VERSION = "2021.8.4"
