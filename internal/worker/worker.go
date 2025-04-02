package worker

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils"
)

type Worker struct {
	Healthcheck     func() bool
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
	pidFile string
	started bool
	killed  bool
	alive   bool
}

func New(healthcheck func() bool) *Worker {
	logger := log.WithField("logger", "authentik.router.worker")
	w := &Worker{
		Healthcheck:     healthcheck,
		log:             logger,
		started:         false,
		killed:          false,
		alive:           false,
		HealthyCallback: func() {},
	}
	w.initCmd()
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGHUP, syscall.SIGUSR2)
	go func() {
		for sig := range c {
			if sig == syscall.SIGHUP {
				w.log.Info("SIGHUP received, forwarding to gunicorn")
				w.Reload()
			} else if sig == syscall.SIGUSR2 {
				w.log.Info("SIGUSR2 received, restarting gunicorn")
				w.Restart()
			}
		}
	}()
	return w
}

func (w *Worker) initCmd() {
	command := "./manage.py"
	args := []string{"dev_server"}
	if !config.Get().Debug {
		pidFile, err := os.CreateTemp("", "authentik-gunicorn.*.pid")
		if err != nil {
			panic(fmt.Errorf("failed to create temporary pid file: %v", err))
		}
		w.pidFile = pidFile.Name()
		command = "gunicorn"
		args = []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
		if w.pidFile != "" {
			args = append(args, "--pid", w.pidFile)
		}
	}
	w.log.WithField("args", args).WithField("cmd", command).Debug("Starting gunicorn")
	w.p = exec.Command(command, args...)
	w.p.Env = os.Environ()
	w.p.Stdout = os.Stdout
	w.p.Stderr = os.Stderr
}

func (w *Worker) IsRunning() bool {
	return w.alive
}

func (w *Worker) Start() error {
	if w.started {
		w.initCmd()
	}
	w.killed = false
	w.started = true
	go w.healthcheck()
	return w.p.Run()
}

func (w *Worker) healthcheck() {
	w.log.Debug("starting healthcheck")
	// Default healthcheck is every 1 second on startup
	// once we've been healthy once, increase to 30 seconds
	for range time.NewTicker(time.Second).C {
		if w.Healthcheck() {
			w.alive = true
			w.log.Debug("backend is alive, backing off with healthchecks")
			w.HealthyCallback()
			break
		}
		w.log.Debug("backend not alive yet")
	}
}

func (w *Worker) Reload() {
	w.log.WithField("method", "reload").Info("reloading gunicorn")
	err := w.p.Process.Signal(syscall.SIGHUP)
	if err != nil {
		w.log.WithError(err).Warning("failed to reload gunicorn")
	}
}

func (w *Worker) Restart() {
	w.log.WithField("method", "restart").Info("restart gunicorn")
	if w.pidFile == "" {
		w.log.Warning("pidfile is non existent, cannot restart")
		return
	}

	err := w.p.Process.Signal(syscall.SIGUSR2)
	if err != nil {
		w.log.WithError(err).Warning("failed to restart gunicorn")
		return
	}

	newPidFile := fmt.Sprintf("%s.2", w.pidFile)

	// Wait for the new PID file to be created
	for range time.NewTicker(1 * time.Second).C {
		_, err = os.Stat(newPidFile)
		if err == nil || !os.IsNotExist(err) {
			break
		}
		w.log.Debugf("waiting for new gunicorn pidfile to appear at %s", newPidFile)
	}
	if err != nil {
		w.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}

	newPidB, err := os.ReadFile(newPidFile)
	if err != nil {
		w.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}
	newPidS := strings.TrimSpace(string(newPidB[:]))
	newPid, err := strconv.Atoi(newPidS)
	if err != nil {
		w.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}
	w.log.Warningf("new gunicorn PID is %d", newPid)

	newProcess, err := utils.FindProcess(newPid)
	if newProcess == nil || err != nil {
		w.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}

	// The new process has started, let's gracefully kill the old one
	w.log.Warning("killing old gunicorn")
	err = w.p.Process.Signal(syscall.SIGTERM)
	if err != nil {
		w.log.Warning("failed to kill old instance of gunicorn")
	}

	w.p.Process = newProcess
	// No need to close any files and the .2 pid file is deleted by Gunicorn
}

func (w *Worker) Kill() {
	if !w.started {
		return
	}
	var err error
	if runtime.GOOS == "darwin" {
		w.log.WithField("method", "kill").Warning("stopping gunicorn")
		err = w.p.Process.Kill()
	} else {
		w.log.WithField("method", "sigterm").Warning("stopping gunicorn")
		err = syscall.Kill(w.p.Process.Pid, syscall.SIGTERM)
	}
	if err != nil {
		w.log.WithError(err).Warning("failed to stop gunicorn")
	}
	if w.pidFile != "" {
		err := os.Remove(w.pidFile)
		if err != nil {
			w.log.WithError(err).Warning("failed to remove pidfile")
		}
	}
	w.killed = true
}
