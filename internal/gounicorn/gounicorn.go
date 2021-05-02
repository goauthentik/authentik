package gounicorn

import (
	"os"
	"os/exec"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

type GoUnicorn struct {
	log *log.Entry
}

func NewGoUnicorn() *GoUnicorn {
	return &GoUnicorn{
		log: log.WithField("logger", "authentik.g.unicorn"),
	}
}

func (g *GoUnicorn) Start() error {
	command := "gunicorn"
	args := []string{"-c", "./lifecycle/gunicorn.conf.py", "authentik.root.asgi:application"}
	if config.G.Debug {
		command = "python"
		args = []string{"manage.py", "runserver", "localhost:8000"}
	}
	g.log.WithField("args", args).WithField("cmd", command).Debug("Starting gunicorn")
	p := exec.Command(command, args...)
	p.Env = append(os.Environ(),
		"WORKERS=2",
	)
	p.Stdout = os.Stdout
	p.Stderr = os.Stderr
	return p.Run()
}
