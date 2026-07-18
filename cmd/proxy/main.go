package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"goauthentik.io/internal/common"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak/entrypoint"
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
	Long:             helpMessage,
	Version:          constants.FullVersion(),
	PersistentPreRun: common.PreRun,
	RunE: func(cmd *cobra.Command, args []string) error {
		err := entrypoint.OutpostMain("authentik.outpost.proxy", proxyv2.NewProxyServer)
		if err != nil {
			fmt.Println(helpMessage)
		}
		return err
	},
}

func main() {
	rootCmd.AddCommand(healthcheck.Command)
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}
