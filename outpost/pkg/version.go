package pkg

import (
	"fmt"
	"os"
)

const VERSION = "2021.5.4"

func BUILD() string {
	build := os.Getenv("GIT_BUILD_HASH")
	if build == "" {
		return "tagged"
	}
	return build
}

func UserAgent() string {
	return fmt.Sprintf("authentik-outpost@%s (%s)", VERSION, BUILD())
}
