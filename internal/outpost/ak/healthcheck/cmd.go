package healthcheck

import (
	"context"
	"net"
	"net/http"
	"os"
	"path"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/ak"
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
		Transport: web.NewUserAgentTransport("goauthentik.io/healthcheck",
			&http.Transport{
				DialContext: func(_ context.Context, _, _ string) (net.Conn, error) {
					return net.Dial("unix", path.Join(os.TempDir(), ak.MetricsSocketName))
				},
			},
		),
	}
	url := "http://localhost/outpost.goauthentik.io/ping"
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
