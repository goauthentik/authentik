package gounicorn

import (
	"os"
	"os/exec"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

type GoUnicorn struct {
	log *log.Entry
	p   *exec.Cmd
}

func NewGoUnicorn() *GoUnicorn {
	logger := log.WithField("logger", "authentik.g.unicorn")
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
	if config.G.Debug {
		command = "python"
		args = []string{"manage.py", "runserver", "localhost:8000"}
	}
	logger.WithField("args", args).WithField("cmd", command).Debug("Starting gunicorn")
	p := exec.Command(command, args...)
	p.Env = append(os.Environ(),
		"WORKERS=2",
	)
	p.Stdout = os.Stdout
	p.Stderr = os.Stderr
	return &GoUnicorn{
		log: logger,
		p:   p,
	}
}

func (g *GoUnicorn) Start() error {
	return g.p.Run()
}

func (g *GoUnicorn) Kill() error {
	return g.p.Process.Kill()
}
