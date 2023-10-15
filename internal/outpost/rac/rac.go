package rac

import (
	"context"
	"os/exec"
	"sync"

	"github.com/mitchellh/mapstructure"
	log "github.com/sirupsen/logrus"
	"github.com/wwt/guac"

	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/rac/connection"
	"goauthentik.io/internal/outpost/rac/metrics"
)

type RACServer struct {
	log   *log.Entry
	ac    *ak.APIController
	guacd *exec.Cmd
	conns map[string]connection.Connection
}

func NewServer(ac *ak.APIController) *RACServer {
	rs := &RACServer{
		log:   log.WithField("logger", "authentik.outpost.rac"),
		ac:    ac,
		conns: map[string]connection.Connection{},
	}
	ac.AddWSHandler(rs.wsHandler)
	return rs
}

type WSMessage struct {
	ConnID        string            `mapstructure:"conn_id"`
	DestChannelID string            `mapstructure:"dest_channel_id"`
	Params        map[string]string `mapstructure:"params"`
	Protocol      string            `mapstructure:"protocol"`
}

func (rs *RACServer) wsHandler(ctx context.Context, args map[string]interface{}) {
	wsm := WSMessage{}
	err := mapstructure.Decode(args, &wsm)
	if err != nil {
		rs.log.WithError(err).Warning("invalid ws message")
		return
	}
	config := guac.NewGuacamoleConfiguration()
	config.Protocol = wsm.Protocol
	rs.log.WithField("params", wsm.Params).Debug("params")
	config.Parameters = wsm.Params
	// config
	cc, err := connection.NewConnection(rs.ac, wsm.DestChannelID, config)
	if err != nil {
		rs.log.WithError(err).Warning("failed to setup connection")
		return
	}
	rs.conns[wsm.ConnID] = *cc
}

func (rs *RACServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		metrics.RunServer()
	}()
	go func() {
		defer wg.Done()
		err := rs.startGuac()
		if err != nil {
			panic(err)
		}
	}()
	wg.Wait()
	return nil
}

func (rs *RACServer) Stop() error {
	if rs.guacd != nil {
		return rs.guacd.Process.Kill()
	}
	return nil
}

func (rs *RACServer) TimerFlowCacheExpiry(context.Context) {}

func (rs *RACServer) Type() string {
	return "rac"
}

func (rs *RACServer) Refresh() error {
	return nil
}
