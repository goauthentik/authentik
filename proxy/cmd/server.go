package cmd

import (
	"math/rand"
	"net/url"
	"os"
	"os/signal"
	"time"

	"github.com/BeryJu/passbook/proxy/pkg/server"
)

// RunServer main entrypoint, runs the full server
func RunServer() {
	pbURL, found := os.LookupEnv("PASSBOOK_HOST")
	if !found {
		panic("env PASSBOOK_HOST not set!")
	}
	pbToken, found := os.LookupEnv("PASSBOOK_TOKEN")
	if !found {
		panic("env PASSBOOK_TOKEN not set!")
	}

	pbURLActual, err := url.Parse(pbURL)
	if err != nil {
		panic(err)
	}

	rand.Seed(time.Now().UnixNano())

	ac := server.NewAPIController(*pbURLActual, pbToken)

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	ac.Start()

	for {
		select {
		case <-interrupt:
			ac.Shutdown()
			os.Exit(0)
		}
	}
}
