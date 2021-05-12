package pkg

import (
	"fmt"
	"os"
)

const VERSION = "2021.5.1-rc8"

func BUILD() string {
	return os.Getenv("GIT_BUILD_HASH")
}

func UserAgent() string {
	return fmt.Sprintf("authentik-outpost@%s (%s)", VERSION, BUILD())
}
