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

	"go.uber.org/zap"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils"
)

type GoUnicorn struct {
	Healthcheck     func() bool
	HealthyCallback func()

	log     *zap.Logger
	p       *exec.Cmd
	pidFile string
	started bool
	killed  bool
	alive   bool
}

func New(healthcheck func() bool) *GoUnicorn {
	logger := config.Get().Logger().Named("authentik.router.unicorn")
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
	g.log.Debug("Starting gunicorn", zap.Strings("args", args), zap.String("cmd", command))
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
	for range time.NewTicker(time.Second).C {
		if g.Healthcheck() {
			g.alive = true
			g.log.Debug("backend is alive, backing off with healthchecks")
			g.HealthyCallback()
			break
		}
		g.log.Debug("backend not alive yet")
	}
}

func (g *GoUnicorn) Reload() {
	g.log.Info("reloading gunicorn", zap.String("method", "reload"))
	err := g.p.Process.Signal(syscall.SIGHUP)
	if err != nil {
		g.log.Warn("failed to reload gunicorn", zap.Error(err))
	}
}

func (g *GoUnicorn) Restart() {
	g.log.Info("restart gunicorn", zap.String("method", "restart"))
	if g.pidFile == "" {
		g.log.Warn("pidfile is non existent, cannot restart")
		return
	}

	err := g.p.Process.Signal(syscall.SIGUSR2)
	if err != nil {
		g.log.Warn("failed to restart gunicorn", zap.Error(err))
		return
	}

	newPidFile := fmt.Sprintf("%s.2", g.pidFile)

	// Wait for the new PID file to be created
	for range time.NewTicker(1 * time.Second).C {
		_, err = os.Stat(newPidFile)
		if err == nil || !os.IsNotExist(err) {
			break
		}
		g.log.Debug("waiting for new gunicorn pidfile to appear", zap.String("path", newPidFile))
	}
	if err != nil {
		g.log.Warn("failed to find the new gunicorn process, aborting", zap.Error(err))
		return
	}

	newPidB, err := os.ReadFile(newPidFile)
	if err != nil {
		g.log.Warn("failed to find the new gunicorn process, aborting", zap.Error(err))
		return
	}
	newPidS := strings.TrimSpace(string(newPidB[:]))
	newPid, err := strconv.Atoi(newPidS)
	if err != nil {
		g.log.Warn("failed to find the new gunicorn process, aborting", zap.Error(err))
		return
	}
	g.log.Warn("new gunicorn PID", zap.Int("pid", newPid))

	newProcess, err := utils.FindProcess(newPid)
	if newProcess == nil || err != nil {
		g.log.Warn("failed to find the new gunicorn process, aborting", zap.Error(err))
		return
	}

	// The new process has started, let's gracefully kill the old one
	g.log.Warn("killing old gunicorn")
	err = g.p.Process.Signal(syscall.SIGTERM)
	if err != nil {
		g.log.Warn("failed to kill old instance of gunicorn")
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
		g.log.Warn("stopping gunicorn", zap.String("method", "kill"))
		err = g.p.Process.Kill()
	} else {
		g.log.Warn("stopping gunicorn", zap.String("method", "sigterm"))
		err = syscall.Kill(g.p.Process.Pid, syscall.SIGTERM)
	}
	if err != nil {
		g.log.Warn("failed to stop gunicorn", zap.Error(err))
	}
	if g.pidFile != "" {
		err := os.Remove(g.pidFile)
		if err != nil {
			g.log.Warn("failed to remove pidfile", zap.Error(err))
		}
	}
	g.killed = true
}
