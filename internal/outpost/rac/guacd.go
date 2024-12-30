package rac

import (
	"os"
	"os/exec"
	"strings"

	"go.uber.org/zap"
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
	sw, _ := zap.NewStdLogAt(rs.log, zap.InfoLevel)
	ew, _ := zap.NewStdLogAt(rs.log, zap.ErrorLevel)
	rs.guacd.Stdout = sw.Writer()
	rs.guacd.Stderr = ew.Writer()
	rs.log.Info("starting guacd")
	return rs.guacd.Start()
}
