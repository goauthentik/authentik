package eap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
)

type context struct {
	req         *radius.Request
	rootPayload protocol.Payload
	typeState   map[protocol.Type]any
	log         *log.Entry
	settings    interface{}
	endStatus   protocol.Status
	endModifier func(p *radius.Packet) *radius.Packet
}

func (ctx *context) RootPayload() protocol.Payload            { return ctx.rootPayload }
func (ctx *context) Packet() *radius.Request                  { return ctx.req }
func (ctx *context) ProtocolSettings() any                    { return ctx.settings }
func (ctx *context) GetProtocolState(p protocol.Type) any     { return ctx.typeState[p] }
func (ctx *context) SetProtocolState(p protocol.Type, st any) { ctx.typeState[p] = st }
func (ctx *context) IsProtocolStart(p protocol.Type) bool     { return ctx.typeState[p] == nil }
func (ctx *context) Log() *log.Entry                          { return ctx.log }
func (ctx *context) HandleInnerEAP(protocol.Payload) protocol.Payload {
	return nil
}

func (ctx *context) ForInnerProtocol(p protocol.Type) protocol.Context {
	return &context{
		req:         ctx.req,
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
