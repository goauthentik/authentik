package main

import (
	"github.com/BeryJu/passbook/proxy/cmd"
	log "github.com/sirupsen/logrus"
)

func main() {
	log.SetLevel(log.DebugLevel)
	cmd.RunServer()
}
