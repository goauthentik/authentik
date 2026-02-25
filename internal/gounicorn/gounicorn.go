package gounicorn

import (
	"goauthentik.io/internal/config"
)

func NewGunicorn(healthcheck func() bool) *Process {
	command := "./manage.py"
	args := []string{"dev_server"}
	if !config.Get().Debug {
		command = "gunicorn"
		args = []string{
			"-c", "./lifecycle/gunicorn.conf.py",
			"authentik.root.asgi:application",
			"--pid", "$PIDFILE",
		}
	}
	return New("gunicorn", command, args, healthcheck)
}
