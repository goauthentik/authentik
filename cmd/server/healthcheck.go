package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"path"
	"strings"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"goauthentik.io/internal/config"
	utils "goauthentik.io/internal/utils/web"
	"goauthentik.io/internal/web"
)

var healthcheckCmd = &cobra.Command{
	Use: "healthcheck",
	Run: func(cmd *cobra.Command, args []string) {
		if len(args) < 1 {
			os.Exit(1)
		}
		mode := args[0]
		exitCode := 1
		log.WithField("mode", mode).Debug("checking health")
		switch strings.ToLower(mode) {
		case "allinone":
			fallthrough
		case "server":
			exitCode = check(fmt.Sprintf("http://localhost%s-/health/live/", config.Get().Web.Path))
		case "worker":
			exitCode = check("http://localhost/-/health/live/")
		default:
			log.Warn("Invalid mode")
		}
		os.Exit(exitCode)
	},
}

func init() {
	rootCmd.AddCommand(healthcheckCmd)
}

func check(url string) int {
	h := &http.Client{
		Transport: utils.NewUserAgentTransport("goauthentik.io/healthcheck",
			&http.Transport{
				DialContext: func(_ context.Context, _, _ string) (net.Conn, error) {
					return net.Dial("unix", path.Join(os.TempDir(), web.SocketName))
				},
			},
		),
	}
	res, err := h.Head(url)
	if err != nil {
		log.WithError(err).Warning("failed to send healthcheck request")
		return 1
	}
	if res.StatusCode >= 400 {
		log.WithField("status", res.StatusCode).Warning("unhealthy status code")
		return 1
	}
	log.Debug("successfully checked health")
	return 0
}
