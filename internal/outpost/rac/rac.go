package rac

import (
	"context"
	"os/exec"
	"strconv"
	"sync"

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
	connm sync.RWMutex
	conns map[string]connection.Connection
}

func NewServer(ac *ak.APIController) ak.Outpost {
	rs := &RACServer{
		log:   log.WithField("logger", "authentik.outpost.rac"),
		ac:    ac,
		connm: sync.RWMutex{},
		conns: map[string]connection.Connection{},
	}
	ac.AddEventHandler(rs.wsHandler)
	return rs
}

type WSMessage struct {
	ConnID              string            `mapstructure:"conn_id"`
	DestChannelID       string            `mapstructure:"dest_channel_id"`
	Params              map[string]string `mapstructure:"params"`
	Protocol            string            `mapstructure:"protocol"`
	OptimalScreenWidth  string            `mapstructure:"screen_width"`
	OptimalScreenHeight string            `mapstructure:"screen_height"`
	OptimalScreenDPI    string            `mapstructure:"screen_dpi"`
}

func parseIntOrZero(input string) int {
	x, err := strconv.Atoi(input)
	if err != nil {
		return 0
	}
	return x
}

func (rs *RACServer) wsHandler(ctx context.Context, msg ak.Event) error {
	if msg.Instruction != ak.EventKindProviderSpecific {
		return nil
	}
	wsm := WSMessage{}
	err := msg.ArgsAs(&wsm)
	if err != nil {
		return err
	}
	config := guac.NewGuacamoleConfiguration()
	config.Protocol = wsm.Protocol
	config.Parameters = wsm.Params
	config.OptimalScreenWidth = parseIntOrZero(wsm.OptimalScreenWidth)
	config.OptimalScreenHeight = parseIntOrZero(wsm.OptimalScreenHeight)
	config.OptimalResolution = parseIntOrZero(wsm.OptimalScreenDPI)
	config.AudioMimetypes = []string{
		"audio/L8",
		"audio/L16",
	}
	cc, err := connection.NewConnection(rs.ac, wsm.DestChannelID, config)
	if err != nil {
		return err
	}
	cc.OnError = func(err error) {
		rs.connm.Lock()
		delete(rs.conns, wsm.ConnID)
		_ = rs.ac.SendEventHello(map[string]interface{}{
			"active_connections": len(rs.conns),
		})
		rs.connm.Unlock()
	}
	rs.connm.Lock()
	rs.conns[wsm.ConnID] = *cc
	_ = rs.ac.SendEventHello(map[string]interface{}{
		"active_connections": len(rs.conns),
	})
	rs.connm.Unlock()
	return nil
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
