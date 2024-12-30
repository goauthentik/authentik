package main

import (
	"fmt"
	"net/url"
	"os"

	"github.com/spf13/cobra"
	"go.uber.org/zap"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/debug"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ak/healthcheck"
	"goauthentik.io/internal/outpost/proxyv2"
)

const helpMessage = `authentik proxy

Required environment variables:
- AUTHENTIK_HOST: URL to connect to (format "http://authentik.company")
- AUTHENTIK_TOKEN: Token to authenticate with
- AUTHENTIK_INSECURE: Skip SSL Certificate verification

Optionally, you can set these:
- AUTHENTIK_HOST_BROWSER: URL to use in the browser, when it differs from AUTHENTIK_HOST`

var rootCmd = &cobra.Command{
	Long: helpMessage,
	Run: func(cmd *cobra.Command, args []string) {
		debug.EnableDebugServer()
		akURL := config.Get().AuthentikHost
		if akURL == "" {
			fmt.Println("env AUTHENTIK_HOST not set!")
			fmt.Println(helpMessage)
			os.Exit(1)
		}
		akToken := config.Get().AuthentikToken
		if akToken == "" {
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

		ac.Server = proxyv2.NewProxyServer(ac)

		err = ac.Start()
		if err != nil {
			config.Get().Logger().Panic("Failed to run server", zap.Error(err))
		}

		for {
			<-ex
		}
	},
}

func main() {
	rootCmd.AddCommand(healthcheck.Command)
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}
