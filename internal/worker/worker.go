package worker

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"syscall"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/config"
)

type Worker struct {
	Healthcheck     func() bool
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
	pidFile string
	started bool
	killed  bool
}

func New() *Worker {
	logger := log.WithField("logger", "authentik.router.worker")
	w := &Worker{
		log:     logger,
		started: false,
		killed:  false,
	}
	w.initCmd()
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGHUP, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		for sig := range c {
			switch sig {
			case syscall.SIGHUP:
				w.log.Info("SIGHUP received, forwarding to dramatiq")
				w.Reload()
			case syscall.SIGINT:
				w.log.Info("SIGINT received, stopping dramatiq")
				w.Kill(syscall.SIGINT)
			case syscall.SIGTERM:
				w.log.Info("SIGTERM received, stopping dramatiq")
				w.Kill(syscall.SIGTERM)
			}
		}
	}()
	return w
}

func (w *Worker) initCmd() {
	command := "./manage.py"
	args := []string{"worker"}
	if config.Get().Debug {
		args = append(args, "--reload")
	}

	pidFile, err := os.CreateTemp("", "authentik-dramatiq.pid")
	if err != nil {
		panic(fmt.Errorf("failed to create temporary pid file: %v", err))
	}
	w.pidFile = pidFile.Name()
	args = append(args, "--pid-file", w.pidFile)

	w.log.WithField("args", args).WithField("cmd", command).Debug("Starting dramatiq")
	w.p = exec.Command(command, args...)
	w.p.Env = os.Environ()
	w.p.Stdout = os.Stdout
	w.p.Stderr = os.Stderr
}

func (w *Worker) Start() error {
	if !w.started {
		w.initCmd()
	}
	w.killed = false
	w.started = true
	return w.p.Run()
}

func (w *Worker) Reload() {
	w.log.WithField("method", "reload").Info("reloading dramatiq")
	err := w.p.Process.Signal(syscall.SIGHUP)
	if err != nil {
		w.log.WithError(err).Warning("failed to reload dramatiq")
	}
}

func (w *Worker) Kill(sig syscall.Signal) {
	if !w.started {
		return
	}
	var err error
	if runtime.GOOS == "darwin" {
		w.log.WithField("method", "processKill").Warning("stopping dramatiq")
		err = w.p.Process.Kill()
	} else {
		w.log.WithField("method", "syscallKill").Warning("stopping dramatiq")
		err = syscall.Kill(w.p.Process.Pid, sig)
	}
	if err != nil {
		w.log.WithError(err).Warning("failed to stop dramatiq")
	}
	if w.pidFile != "" {
		err := os.Remove(w.pidFile)
		if err != nil {
			w.log.WithError(err).Warning("failed to remove pidfile")
		}
	}
	w.killed = true
}
