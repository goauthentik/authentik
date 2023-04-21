package healthcheck

import (
	"fmt"
	"net/http"
	"os"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/web"
)

var Command = &cobra.Command{
	Use: "healthcheck",
	Run: func(cmd *cobra.Command, args []string) {
		config.Get()
		os.Exit(check())
	},
}

func check() int {
	h := &http.Client{
		Transport: web.NewUserAgentTransport("goauthentik.io/healthcheck", http.DefaultTransport),
	}
	url := fmt.Sprintf("http://%s/outpost.goauthentik.io/ping", config.Get().Listen.Metrics)
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
