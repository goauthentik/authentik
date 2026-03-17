package main

import (
	"fmt"
	"net/http"
	"os"
	"path"
	"strconv"
	"strings"
	"syscall"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/web"
)

var workerPidFile = path.Join(os.TempDir(), "authentik-worker.pid")

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
	url := fmt.Sprintf("http://%s%s-/health/live/", config.Get().Listen.HTTP, config.Get().Web.Path)
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
	pidB, err := os.ReadFile(workerPidFile)
	if err != nil {
		log.WithError(err).Warning("failed to check worker PID file")
		return 1
	}
	pidS := strings.TrimSpace(string(pidB[:]))
	pid, err := strconv.Atoi(pidS)
	if err != nil {
		log.WithError(err).Warning("failed to find worker process PID")
		return 1
	}
	process, err := os.FindProcess(pid)
	if err != nil {
		log.WithError(err).Warning("failed to find worker process")
		return 1
	}
	err = process.Signal(syscall.Signal(0))
	if err != nil {
		log.WithError(err).Warning("failed to signal worker process")
		return 1
	}
	log.Info("successfully checked health")
	return 0
}
