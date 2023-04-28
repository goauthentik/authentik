package gounicorn

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils"
	"goauthentik.io/internal/utils/web"
)

type GoUnicorn struct {
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
	pidFile *string
	started bool
	killed  bool
	alive   bool
}

func New() *GoUnicorn {
	logger := log.WithField("logger", "authentik.router.unicorn")
	g := &GoUnicorn{
		log:             logger,
		pidFile:         nil,
		started:         false,
		killed:          false,
		alive:           false,
		HealthyCallback: func() {},
	}
	g.initCmd()
	return g
}

func (g *GoUnicorn) initCmd() {
	pidFile, _ := os.CreateTemp("", "authentik-gunicorn.*.pid")
	g.pidFile = func() *string { s := pidFile.Name(); return &s }()
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
	if g.pidFile != nil {
		args = append(args, "--pid", *g.pidFile)
	}
	if config.Get().Debug {
		command = "./manage.py"
		args = []string{"runserver"}
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
	return g.p.Start()
}

func (g *GoUnicorn) healthcheck() {
	g.log.Debug("starting healthcheck")
	h := &http.Client{
		Transport: web.NewUserAgentTransport("goauthentik.io/proxy/healthcheck", http.DefaultTransport),
	}
	check := func() bool {
		res, err := h.Get("http://localhost:8000/-/health/live/")
		if err == nil && res.StatusCode == 204 {
			g.alive = true
			return true
		}
		return false
	}

	// Default healthcheck is every 1 second on startup
	// once we've been healthy once, increase to 30 seconds
	for range time.Tick(time.Second) {
		if check() {
			g.log.Info("backend is alive, backing off with healthchecks")
			g.HealthyCallback()
			break
		}
		g.log.Debug("backend not alive yet")
	}
	for range time.Tick(30 * time.Second) {
		check()
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
	if g.pidFile == nil {
		g.log.Warning("pidfile is non existent, cannot restart")
		return
	}

	err := g.p.Process.Signal(syscall.SIGUSR2)
	if err != nil {
		g.log.WithError(err).Warning("failed to restart gunicorn")
		return
	}

	newPidFile := fmt.Sprintf("%s.2", *g.pidFile)

	// Wait for the new PID file to be created
	for range time.Tick(1 * time.Second) {
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

	newPidB, err := ioutil.ReadFile(newPidFile)
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
	g.log.Warningf("killing old gunicorn")
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
	if g.pidFile != nil {
		os.Remove(*g.pidFile)
	}
	g.killed = true
}
