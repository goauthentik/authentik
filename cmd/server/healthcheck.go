package main

import (
	"fmt"
	"net/http"
	"os"
	"path"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"go.uber.org/zap"
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
		l := config.Get().Logger().Named("authentik.server.healthcheck")
		l.Debug("checking health", zap.String("mode", mode))
		switch strings.ToLower(mode) {
		case "server":
			exitCode = checkServer(l)
		case "worker":
			exitCode = checkWorker(l)
		default:
			l.Warn("Invalid mode", zap.String("mode", mode))
		}
		os.Exit(exitCode)
	},
}

func init() {
	rootCmd.AddCommand(healthcheckCmd)
}

func checkServer(l *zap.Logger) int {
	h := &http.Client{
		Transport: web.NewUserAgentTransport("goauthentik.io/healthcheck", http.DefaultTransport),
	}
	url := fmt.Sprintf("http://%s%s-/health/live/", config.Get().Listen.HTTP, config.Get().Web.Path)
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

func checkWorker(l *zap.Logger) int {
	stat, err := os.Stat(workerHeartbeat)
	if err != nil {
		l.Warn("failed to check worker heartbeat file", zap.Error(err))
		return 1
	}
	delta := time.Since(stat.ModTime()).Seconds()
	if delta > workerThreshold {
		l.Warn("Worker hasn't updated heartbeat in threshold", zap.Int("threshold", workerThreshold), zap.Float64("delta", delta))
		return 1
	}
	return 0
}
