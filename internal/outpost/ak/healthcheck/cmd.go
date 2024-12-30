package healthcheck

import (
	"fmt"
	"net/http"
	"os"

	"github.com/spf13/cobra"
	"go.uber.org/zap"
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
	l := config.Get().Logger()
	url := fmt.Sprintf("http://%s/outpost.goauthentik.io/ping", config.Get().Listen.Metrics)
	res, err := h.Head(url)
	if err != nil {
		l.Warn("failed to send healthcheck request", zap.Error(err))
		return 1
	}
	if res.StatusCode >= 400 {
		l.Warn("unhealthy status code", zap.Int("status", res.StatusCode))
		return 1
	}
	l.Debug("successfully checked health")
	return 0
}
