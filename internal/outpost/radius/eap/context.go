package eap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
)

type context struct {
	req         *radius.Request
	state       interface{}
	typeState   map[protocol.Type]any
	log         *log.Entry
	settings    interface{}
	endStatus   protocol.Status
	endModifier func(p *radius.Packet) *radius.Packet
}

func (ctx *context) Packet() *radius.Request                      { return ctx.req }
func (ctx *context) ProtocolSettings() interface{}                { return ctx.settings }
func (ctx *context) StateForProtocol(p protocol.Type) interface{} { return ctx.typeState[p] }
func (ctx *context) GetProtocolState() interface{}                { return ctx.state }
func (ctx *context) SetProtocolState(st interface{})              { ctx.state = st }
func (ctx *context) IsProtocolStart() bool                        { return ctx.state == nil }
func (ctx *context) Log() *log.Entry                              { return ctx.log }

func (ctx *context) ForInnerProtocol(p protocol.Type) protocol.Context {
	log.Debug("foo")
	log.Debugf("%+v", ctx.typeState[protocol.Type(13)])
	log.Debugf("%+v", ctx.typeState[protocol.Type(25)])
	return &context{
		req:         ctx.req,
		state:       ctx.StateForProtocol(p),
		typeState:   ctx.typeState,
		log:         ctx.log,
		settings:    ctx.settings,
		endStatus:   ctx.endStatus,
		endModifier: ctx.endModifier,
	}
}

func (ctx *context) EndInnerProtocol(st protocol.Status, mf func(p *radius.Packet) *radius.Packet) {
	if ctx.endStatus != protocol.StatusUnknown {
		return
	}
	ctx.endStatus = st
	if mf == nil {
		mf = func(p *radius.Packet) *radius.Packet {
			return p
		}
	}
	ctx.endModifier = mf
}
