package gounicorn

import (
	"os"
	"os/exec"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

type GoUnicorn struct {
	log     *log.Entry
	p       *exec.Cmd
	started bool
	killed  bool
}

func NewGoUnicorn() *GoUnicorn {
	logger := log.WithField("logger", "authentik.g.unicorn")
	g := &GoUnicorn{
		log:     logger,
		started: false,
		killed:  false,
	}
	g.initCmd()
	return g
}

func (g *GoUnicorn) initCmd() {
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
	if config.G.Debug {
		command = "python"
		args = []string{"manage.py", "runserver", "localhost:8000"}
	}
	g.log.WithField("args", args).WithField("cmd", command).Debug("Starting gunicorn")
	g.p = exec.Command(command, args...)
	g.p.Env = os.Environ()
	g.p.Stdout = os.Stdout
	g.p.Stderr = os.Stderr
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
	return g.p.Run()
}

func (g *GoUnicorn) Kill() {
	g.killed = true
	err := g.p.Process.Kill()
	if err != nil {
		g.log.WithError(err).Warning("failed to kill gunicorn")
	}
}
