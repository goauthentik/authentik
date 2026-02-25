package gounicorn

func NewWorker(healthcheck func() bool) *Process {
	command := "./manage.py"
	args := []string{"worker", "--pid-file", "$PIDFILE"}
	return New("worker", command, args, healthcheck)
}
