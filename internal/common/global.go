package common

import (
	"math/rand"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/getsentry/sentry-go"
)

func Init() chan os.Signal {
	rand.Seed(time.Now().UnixNano())
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
