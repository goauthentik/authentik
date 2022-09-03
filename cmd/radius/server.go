package main

import (
	"fmt"
	"net/url"
	"os"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/radius"
)

const helpMessage = `authentik radius

Required environment variables:
- AUTHENTIK_HOST: URL to connect to (format "http://authentik.company")
- AUTHENTIK_TOKEN: Token to authenticate with
- AUTHENTIK_INSECURE: Skip SSL Certificate verification`

func main() {
	log.SetLevel(log.DebugLevel)
	log.SetFormatter(&log.JSONFormatter{
		FieldMap: log.FieldMap{
			log.FieldKeyMsg:  "event",
			log.FieldKeyTime: "timestamp",
		},
		DisableHTMLEscape: true,
	})
	go debug.EnableDebugServer()
	akURL, found := os.LookupEnv("AUTHENTIK_HOST")
	if !found {
		fmt.Println("env AUTHENTIK_HOST not set!")
		fmt.Println(helpMessage)
		os.Exit(1)
	}
	akToken, found := os.LookupEnv("AUTHENTIK_TOKEN")
	if !found {
		fmt.Println("env AUTHENTIK_TOKEN not set!")
		fmt.Println(helpMessage)
		os.Exit(1)
	}

	akURLActual, err := url.Parse(akURL)
	if err != nil {
		fmt.Println(err)
		fmt.Println(helpMessage)
		os.Exit(1)
	}

	ex := common.Init()
	defer common.Defer()
	go func() {
		for {
			<-ex
			os.Exit(0)
		}
	}()

	ac := ak.NewAPIController(*akURLActual, akToken)
	if ac == nil {
		os.Exit(1)
	}
	defer ac.Shutdown()

	ac.Server = radius.NewServer(ac)

	err = ac.Start()
	if err != nil {
		log.WithError(err).Panic("Failed to run server")
	}

	for {
		<-ex
	}
}
