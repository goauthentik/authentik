package gounicorn

import (
	"fmt"
	"math/rand/v2"
	"os"
	"os/exec"
	"os/signal"
	"path"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/utils"
)

type Process struct {
	Healthcheck      func() bool
	healthyCallbacks []func()
	name             string
	cmd              string
	args             []string
	log              *log.Entry
	p                *exec.Cmd
	pidFile          string
	started          bool
	killed           bool
	alive            bool
}

func New(name string, cmd string, args []string, healthcheck func() bool) *Process {
	logger := log.WithField("logger", fmt.Sprintf("authentik.router.proc_%s", name))
	g := &Process{
		Healthcheck:      healthcheck,
		name:             name,
		log:              logger,
		cmd:              cmd,
		args:             args,
		started:          false,
		killed:           false,
		alive:            false,
		healthyCallbacks: []func(){},
	}
	g.initCmd()
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGHUP, syscall.SIGUSR2)
	go func() {
		for sig := range c {
			switch sig {
			case syscall.SIGHUP:
				g.log.Info("SIGHUP received, forwarding to process")
				g.Reload()
			case syscall.SIGUSR2:
				g.log.Info("SIGUSR2 received, restarting process")
				g.Restart()
			}
		}
	}()
	return g
}

func (g *Process) initCmd() {
	for i, arg := range g.args {
		if arg == "$PIDFILE" {
			pidName := path.Join(os.TempDir(), fmt.Sprintf("authentik-%s.%d.pid", g.name, rand.IntN(100)))
			g.pidFile = pidName
			g.args[i] = g.pidFile
		}
	}
	g.log.WithField("args", g.args).WithField("cmd", g.cmd).Debug("Starting process")
	g.p = exec.Command(g.cmd, g.args...)
	g.p.Env = os.Environ()
	g.p.Stdout = os.Stdout
	g.p.Stderr = os.Stderr
}

func (g *Process) AddHealthyCallback(cb func()) {
	g.healthyCallbacks = append(g.healthyCallbacks, cb)
}

func (g *Process) IsRunning() bool {
	return g.alive
}

func (g *Process) Start() error {
	if g.started {
		g.initCmd()
	}
	g.killed = false
	g.started = true
	go g.healthcheck()
	return g.p.Run()
}

func (g *Process) healthcheck() {
	g.log.Debug("starting healthcheck")
	// Default healthcheck is every 1 second on startup
	// once we've been healthy once, increase to 30 seconds
	for range time.NewTicker(time.Second).C {
		if g.Healthcheck() {
			g.alive = true
			g.log.Debug("backend is alive, backing off with healthchecks")
			for _, cb := range g.healthyCallbacks {
				cb()
			}
			break
		}
		g.log.Debug("backend not alive yet")
	}
}

func (g *Process) Reload() {
	g.log.WithField("method", "reload").Info("reloading process")
	err := g.p.Process.Signal(syscall.SIGHUP)
	if err != nil {
		g.log.WithError(err).Warning("failed to reload process")
	}
}

func (g *Process) Restart() {
	g.log.WithField("method", "restart").Info("restart process")
	if g.pidFile == "" {
		g.log.Warning("pidfile is non existent, cannot restart")
		return
	}

	err := g.p.Process.Signal(syscall.SIGUSR2)
	if err != nil {
		g.log.WithError(err).Warning("failed to restart process")
		return
	}

	newPidFile := fmt.Sprintf("%s.2", g.pidFile)

	// Wait for the new PID file to be created
	for range time.NewTicker(1 * time.Second).C {
		_, err = os.Stat(newPidFile)
		if err == nil || !os.IsNotExist(err) {
			break
		}
		g.log.Debugf("waiting for new process pidfile to appear at %s", newPidFile)
	}
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new process process, aborting")
		return
	}

	newPidB, err := os.ReadFile(newPidFile)
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new process process, aborting")
		return
	}
	newPidS := strings.TrimSpace(string(newPidB[:]))
	newPid, err := strconv.Atoi(newPidS)
	if err != nil {
		g.log.WithError(err).Warning("failed to find the new process process, aborting")
		return
	}
	g.log.Warningf("new process PID is %d", newPid)

	newProcess, err := utils.FindProcess(newPid)
	if newProcess == nil || err != nil {
		g.log.WithError(err).Warning("failed to find the new process process, aborting")
		return
	}

	// The new process has started, let's gracefully kill the old one
	g.log.Warning("killing old process")
	err = g.p.Process.Signal(syscall.SIGTERM)
	if err != nil {
		g.log.Warning("failed to kill old instance of process")
	}

	g.p.Process = newProcess
	// No need to close any files and the .2 pid file is deleted by process
}

func (g *Process) Kill() {
	if !g.started {
		return
	}
	var err error
	if runtime.GOOS == "darwin" {
		g.log.WithField("method", "kill").Warning("stopping process")
		err = g.p.Process.Kill()
	} else {
		g.log.WithField("method", "sigterm").Warning("stopping process")
		err = syscall.Kill(g.p.Process.Pid, syscall.SIGTERM)
	}
	if err != nil {
		g.log.WithError(err).Warning("failed to stop process")
	}
	if g.pidFile != "" {
		err := os.Remove(g.pidFile)
		if err != nil {
			g.log.WithError(err).Warning("failed to remove pidfile")
		}
	}
	g.killed = true
}
