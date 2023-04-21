package main

import (
	"fmt"
	"net/http"
	"os"
	"path"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/web"
)

var workerHeartbeat = path.Join(os.TempDir(), "authentik-worker")

const workerThreshold = 30

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
		case "server":
			exitCode = checkServer()
		case "worker":
			exitCode = checkWorker()
		default:
			log.Warn("Invalid mode")
		}
		os.Exit(exitCode)
	},
}

func init() {
	rootCmd.AddCommand(healthcheckCmd)
}

func checkServer() int {
	h := &http.Client{
		Transport: web.NewUserAgentTransport("goauthentik.io/healthcheck", http.DefaultTransport),
	}
	url := fmt.Sprintf("http://%s/-/health/ready/", config.Get().Listen.HTTP)
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

func checkWorker() int {
	stat, err := os.Stat(workerHeartbeat)
	if err != nil {
		log.WithError(err).Warning("failed to check worker heartbeat file")
		return 1
	}
	delta := time.Since(stat.ModTime()).Seconds()
	if delta > workerThreshold {
		log.WithField("threshold", workerThreshold).WithField("delta", delta).Warning("Worker hasn't updated heartbeat in threshold")
		return 1
	}
	return 0
}
