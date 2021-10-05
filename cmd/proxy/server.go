package main

import (
	"fmt"
	"net/url"
	"os"
	"strconv"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2"
)

const helpMessage = `authentik proxy

Required environment variables:
- AUTHENTIK_HOST: URL to connect to (format "http://authentik.company")
- AUTHENTIK_TOKEN: Token to authenticate with
- AUTHENTIK_INSECURE: Skip SSL Certificate verification

Optionally, you can set these:
- AUTHENTIK_HOST_BROWSER: URL to use in the browser, when it differs from AUTHENTIK_HOST
- AUTHENTIK_PORT_OFFSET: Offset to add to the listening ports, i.e. value of 100 makes proxy listen on 9100`

func main() {
	log.SetLevel(log.DebugLevel)
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
	portOffset := 0
	portOffsetS := os.Getenv("AUTHENTIK_PORT_OFFSET")
	if portOffsetS != "" {
		v, err := strconv.Atoi(portOffsetS)
		if err != nil {
			fmt.Println(err.Error())
		}
		portOffset = v
	}

	akURLActual, err := url.Parse(akURL)
	if err != nil {
		fmt.Println(err)
		fmt.Println(helpMessage)
		os.Exit(1)
	}

	ex := common.Init()
	defer common.Defer()

	ac := ak.NewAPIController(*akURLActual, akToken)
	if ac == nil {
		os.Exit(1)
	}

	ac.Server = proxyv2.NewProxyServer(ac, portOffset)

	err = ac.Start()
	if err != nil {
		log.WithError(err).Panic("Failed to run server")
	}

	for {
		<-ex
		ac.Shutdown()
		os.Exit(0)
	}
}
