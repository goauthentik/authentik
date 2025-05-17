package common

import (
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/getsentry/sentry-go"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

func PreRun(cmd *cobra.Command, args []string) {
	log.SetLevel(log.DebugLevel)
	log.SetFormatter(&log.JSONFormatter{
		FieldMap: log.FieldMap{
			log.FieldKeyMsg:  "event",
			log.FieldKeyTime: "timestamp",
		},
		DisableHTMLEscape: true,
	})
}

func Init() chan os.Signal {
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)
	signal.Notify(interrupt, syscall.SIGINT)
	signal.Notify(interrupt, syscall.SIGTERM)
	return interrupt
}

func Defer() {
	sentry.Flush(time.Second * 5)
	sentry.Recover()
}
