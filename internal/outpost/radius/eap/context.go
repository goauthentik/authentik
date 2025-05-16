package eap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
)

type context struct {
	req         *radius.Request
	state       interface{}
	log         *log.Entry
	settings    interface{}
	endStatus   protocol.Status
	endModifier func(p *radius.Packet) *radius.Packet
}

func (ctx context) Packet() *radius.Request {
	return ctx.req
}

func (ctx context) ProtocolSettings() interface{} {
	return ctx.settings
}

func (ctx *context) GetProtocolState(def func(protocol.Context) interface{}) interface{} {
	if ctx.state == nil {
		ctx.state = def(ctx)
	}
	return ctx.state
}

func (ctx *context) SetProtocolState(st interface{}) {
	ctx.state = st
}

func (ctx *context) EndInnerProtocol(st protocol.Status, mf func(p *radius.Packet) *radius.Packet) {
	if ctx.endStatus != protocol.StatusUnknown {
		return
	}
	ctx.endStatus = st
	ctx.endModifier = mf
}

func (ctx context) Log() *log.Entry {
	return ctx.log
}
