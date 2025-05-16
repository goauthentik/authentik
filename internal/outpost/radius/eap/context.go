package eap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
)

type context struct {
	state interface{}
	log   *log.Entry
}

func (ctx context) ProtocolSettings() interface{} {
	return nil
}

func (ctx context) GetProtocolState(def func(protocol.Context) interface{}) interface{} {
	return ctx.state
}

func (ctx context) SetProtocolState(st interface{}) {
	ctx.state = st
}

func (ctx context) EndInnerProtocol(func(p *radius.Packet) *radius.Packet) {

}

func (ctx context) Log() *log.Entry {
	return ctx.log
}
