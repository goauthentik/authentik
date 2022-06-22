package gounicorn

import (
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/utils/web"
)

type GoUnicorn struct {
	HealthyCallback func()

	log     *log.Entry
	p       *exec.Cmd
	started bool
	killed  bool
	alive   bool
}

func NewGoUnicorn() *GoUnicorn {
	logger := log.WithField("logger", "authentik.router.unicorn")
	g := &GoUnicorn{
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
	if config.G.Debug {
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
