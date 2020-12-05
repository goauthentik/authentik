package cmd

import (
	"fmt"
	"math/rand"
	"net/url"
	"os"
	"os/signal"
	"time"

	"github.com/BeryJu/authentik/proxy/pkg/server"
)

const helpMessage = `authentik proxy

Required environment variables:
 - AUTHENTIK_HOST: URL to connect to (format "http://authentik.company")
 - AUTHENTIK_TOKEN: Token to authenticate with
 - AUTHENTIK_INSECURE: Skip SSL Certificate verification`

// RunServer main entrypoint, runs the full server
func RunServer() {
	pbURL, found := os.LookupEnv("AUTHENTIK_HOST")
	if !found {
		fmt.Println("env AUTHENTIK_HOST not set!")
		fmt.Println(helpMessage)
		os.Exit(1)
	}
	pbToken, found := os.LookupEnv("AUTHENTIK_TOKEN")
	if !found {
		fmt.Println("env AUTHENTIK_TOKEN not set!")
		fmt.Println(helpMessage)
		os.Exit(1)
	}

	pbURLActual, err := url.Parse(pbURL)
	if err != nil {
		fmt.Println(err)
		fmt.Println(helpMessage)
		os.Exit(1)
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
