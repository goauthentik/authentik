package rac

import (
	"context"
	"os"
	"os/exec"
	"strings"

	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/ak"
)

const guacdPath = "/opt/guacamole/sbin/guacd"
const guacdArgs = " -b 0.0.0.0 -L info -f"

type RACServer struct {
	log *log.Entry
	ac  *ak.APIController
	p   *exec.Cmd
}

func NewServer(ac *ak.APIController) *RACServer {
	rs := &RACServer{
		log: log.WithField("logger", "authentik.outpost.rac"),
		ac:  ac,
	}
	return rs
}

func (rs *RACServer) Start() error {
	rs.p = exec.Command(guacdPath, strings.Split(guacdArgs, " ")...)
	rs.p.Env = os.Environ()
	rs.p.Stdout = rs.log.WithField("logger", "authentik.outpost.rac.guacd").Writer()
	rs.p.Stderr = rs.log.WithField("logger", "authentik.outpost.rac.guacd").WriterLevel(log.WarnLevel)
	go rs.p.Start()
	return nil
}

func (rs *RACServer) Stop() error {
	return nil
}

func (rs *RACServer) TimerFlowCacheExpiry(context.Context) {}

func (rs *RACServer) Type() string {
	return "rac"
}

func (rs *RACServer) Refresh() error {
	return nil
}
