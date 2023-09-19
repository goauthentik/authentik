package gounicorn

import (
	"os"
	"os/exec"
	"runtime"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

type GoUnicorn struct {
	Healthcheck     func() bool
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
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
	return g
}

func (g *GoUnicorn) initCmd() {
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
	if config.Get().Debug {
		command = "./manage.py"
		args = []string{"dev_server"}
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
	if g.killed {
		g.log.Debug("Not restarting gunicorn since we're shutdown")
		return nil
	}
	if g.started {
		g.initCmd()
	}
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

func (g *GoUnicorn) Kill() {
	g.killed = true
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
}
