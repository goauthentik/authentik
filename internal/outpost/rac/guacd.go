package rac

import (
	"os"
	"os/exec"
	"strings"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

const guacdPath = "/opt/guacamole/sbin/guacd"
const guacdArgs = " -b 0.0.0.0 -L debug -f"

func (rs *RACServer) startGuac() error {
	rs.guacd = exec.Command(guacdPath, strings.Split(guacdArgs, " ")...)
	rs.guacd.Env = os.Environ()
	if config.Get().Debug {
		rs.guacd.Stdout = os.Stdout
		rs.guacd.Stderr = os.Stderr
	} else {
		rs.guacd.Stdout = rs.log.WithField("logger", "authentik.outpost.rac.guacd").WriterLevel(log.InfoLevel)
		rs.guacd.Stderr = rs.log.WithField("logger", "authentik.outpost.rac.guacd").WriterLevel(log.WarnLevel)
	}
	rs.log.Info("starting guacd")
	return rs.guacd.Start()
}
