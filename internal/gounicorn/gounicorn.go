package gounicorn

import (
	"net/http"
	"os"
	"os/exec"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ak"
)

type GoUnicorn struct {
	log     *log.Entry
	p       *exec.Cmd
	started bool
	killed  bool
	alive   bool
}

func NewGoUnicorn() *GoUnicorn {
	logger := log.WithField("logger", "authentik.g.unicorn")
	g := &GoUnicorn{
		log:     logger,
		started: false,
		killed:  false,
		alive:   false,
	}
	g.initCmd()
	return g
}

func (g *GoUnicorn) initCmd() {
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi.app:application"}
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
		g.log.Debug("Not restarting gunicorn since we're killed")
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
		Transport: ak.NewUserAgentTransport("goauthentik.io go proxy healthcheck", http.DefaultTransport),
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
	err := g.p.Process.Kill()
	if err != nil {
		g.log.WithError(err).Warning("failed to kill gunicorn")
	}
}
