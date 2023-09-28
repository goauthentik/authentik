package gounicorn

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

type GoUnicorn struct {
	Healthcheck     func() bool
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
	pidFile string
	started bool
	killed  bool
	alive   bool
}

func New(healthcheck func() bool) *GoUnicorn {
	logger := log.WithField("logger", "authentik.router.unicorn")
	g := &GoUnicorn{
		Healthcheck:     healthcheck,
		log:             logger,
		started:         false,
		killed:          false,
		alive:           false,
		HealthyCallback: func() {},
	}
	g.initCmd()
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGHUP, syscall.SIGUSR2)
	go func() {
		for sig := range c {
			if sig == syscall.SIGHUP {
				g.log.Info("SIGHUP received, forwarding to gunicorn")
				g.Reload()
			} else if sig == syscall.SIGUSR2 {
				g.log.Info("SIGUSR2 received, restarting gunicorn")
				g.Restart()
			}
		}
	}()
	return g
}

func (g *GoUnicorn) initCmd() {
	command := "./manage.py"
	args := []string{"dev_server"}
	if !config.Get().Debug {
		pidFile, err := os.CreateTemp("", "authentik-gunicorn.*.pid")
		if err != nil {
			panic(fmt.Errorf("failed to create temporary pid file: %v", err))
		}
		g.pidFile = pidFile.Name()
		command = "gunicorn"
		args = []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
		if g.pidFile != "" {
			args = append(args, "--pid", g.pidFile)
		}
	}
	g.log.WithField("args", args).WithField("cmd", command).Debug("Starting gunicorn")
	g.p = exec.Command(command, args...)
	g.p.Env = os.Environ()
	g.p.Stdout = os.Stdout
	g.p.Stderr = os.Stderr
}

func (g *GoUnicorn) IsRunning() bool {
	return g.alive
}

func (g *GoUnicorn) Start() error {
	if g.started {
		g.initCmd()
	}
	g.killed = false
	g.started = true
	go g.healthcheck()
	return g.p.Run()
}

func (g *GoUnicorn) healthcheck() {
	g.log.Debug("starting healthcheck")
	// Default healthcheck is every 1 second on startup
	// once we've been healthy once, increase to 30 seconds
	for range time.Tick(time.Second) {
		if g.Healthcheck() {
			g.alive = true
			g.log.Info("backend is alive, backing off with healthchecks")
			g.HealthyCallback()
			break
		}
		g.log.Debug("backend not alive yet")
	}
	for range time.Tick(30 * time.Second) {
		g.Healthcheck()
	}
}

func (g *GoUnicorn) Reload() {
	g.log.WithField("method", "reload").Info("reloading gunicorn")
	err := g.p.Process.Signal(syscall.SIGHUP)
	if err != nil {
		g.log.WithError(err).Warning("failed to reload gunicorn")
	}
}

func (g *GoUnicorn) Restart() {
	g.log.WithField("method", "restart").Info("restart gunicorn")
	if g.pidFile == "" {
		g.log.Warning("pidfile is non existent, cannot restart")
		return
	}

	err := g.p.Process.Signal(syscall.SIGUSR2)
	if err != nil {
		g.log.WithError(err).Warning("failed to restart gunicorn")
		return
	}

	newPidFile := fmt.Sprintf("%s.2", g.pidFile)

	// Wait for the new PID file to be created
	for range time.NewTicker(1 * time.Second).C {
		_, err = os.Stat(newPidFile)
		if err == nil || !os.IsNotExist(err) {
			break
		}
		g.log.Debugf("waiting for new gunicorn pidfile to appear at %s", newPidFile)
	}
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}

	newPidB, err := os.ReadFile(newPidFile)
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}
	newPidS := strings.TrimSpace(string(newPidB[:]))
	newPid, err := strconv.Atoi(newPidS)
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}
	g.log.Warningf("new gunicorn PID is %d", newPid)

	newProcess, err := utils.FindProcess(newPid)
	if newProcess == nil || err != nil {
		g.log.WithError(err).Warning("failed to find the new gunicorn process, aborting")
		return
	}

	// The new process has started, let's gracefully kill the old one
	g.log.Warning("killing old gunicorn")
	err = g.p.Process.Signal(syscall.SIGTERM)
	if err != nil {
		g.log.Warning("failed to kill old instance of gunicorn")
	}

	g.p.Process = newProcess
	// No need to close any files and the .2 pid file is deleted by Gunicorn
}

func (g *GoUnicorn) Kill() {
	if !g.started {
		return
	}
	var err error
	if runtime.GOOS == "darwin" {
		g.log.WithField("method", "kill").Warning("stopping gunicorn")
		err = g.p.Process.Kill()
	} else {
		g.log.WithField("method", "sigterm").Warning("stopping gunicorn")
		err = syscall.Kill(g.p.Process.Pid, syscall.SIGTERM)
	}
	if err != nil {
		g.log.WithError(err).Warning("failed to stop gunicorn")
	}
	if g.pidFile != "" {
		err := os.Remove(g.pidFile)
		if err != nil {
			g.log.WithError(err).Warning("failed to remove pidfile")
		}
	}
	g.killed = true
}
