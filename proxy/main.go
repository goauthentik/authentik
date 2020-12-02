package main

import (
	"github.com/BeryJu/authentik/proxy/cmd"
	log "github.com/sirupsen/logrus"
)

func main() {
	log.SetLevel(log.DebugLevel)
	cmd.RunServer()
}
