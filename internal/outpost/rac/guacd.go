package rac

import (
	"os"
	"os/exec"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ak"
)

const (
	guacdPath        = "/opt/guacamole/sbin/guacd"
	guacdDefaultArgs = " -b 0.0.0.0 -f"
)

func (rs *RACServer) startGuac() error {
	guacdArgs := strings.Split(guacdDefaultArgs, " ")
	guacdArgs = append(guacdArgs, "-L", rs.ac.Outpost.Config[ak.ConfigLogLevel].(string))
	rs.guacd = exec.Command(guacdPath, guacdArgs...)
	rs.guacd.Env = os.Environ()
	rs.guacd.Stdout = rs.log.WithField("logger", "authentik.outpost.rac.guacd").WriterLevel(log.InfoLevel)
	rs.guacd.Stderr = rs.log.WithField("logger", "authentik.outpost.rac.guacd").WriterLevel(log.InfoLevel)
	rs.log.Info("starting guacd")
	return rs.guacd.Start()
}
