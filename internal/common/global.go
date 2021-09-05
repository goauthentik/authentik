package common

import (
	"math/rand"
	"os"
	"os/signal"
	"time"

	"github.com/getsentry/sentry-go"
)

func Init() chan os.Signal {
	rand.Seed(time.Now().UnixNano())
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)
	return interrupt
}

func Defer() {
	sentry.Flush(time.Second * 5)
	sentry.Recover()
}
