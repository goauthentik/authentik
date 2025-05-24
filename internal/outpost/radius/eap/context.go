package eap

import (
	"fmt"

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
	parent      *context
	endStatus   protocol.Status
	endModifier func(p *radius.Packet) *radius.Packet
	handleInner func(protocol.Payload, protocol.StateManager) (protocol.Payload, error)
}

func (ctx *context) RootPayload() protocol.Payload            { return ctx.rootPayload }
func (ctx *context) Packet() *radius.Request                  { return ctx.req }
func (ctx *context) ProtocolSettings() any                    { return ctx.settings }
func (ctx *context) GetProtocolState(p protocol.Type) any     { return ctx.typeState[p] }
func (ctx *context) SetProtocolState(p protocol.Type, st any) { ctx.typeState[p] = st }
func (ctx *context) IsProtocolStart(p protocol.Type) bool     { return ctx.typeState[p] == nil }
func (ctx *context) Log() *log.Entry                          { return ctx.log }
func (ctx *context) HandleInnerEAP(p protocol.Payload, st protocol.StateManager) (protocol.Payload, error) {
	return ctx.handleInner(p, st)
}
func (ctx *context) Inner(p protocol.Payload, t protocol.Type) protocol.Context {
	return &context{
		req:         ctx.req,
		rootPayload: ctx.rootPayload,
		typeState:   ctx.typeState,
		log:         ctx.log.WithField("type", fmt.Sprintf("%T", p)).WithField("code", t),
		settings:    ctx.settings,
		parent:      ctx,
		handleInner: ctx.handleInner,
	}
}
func (ctx *context) EndInnerProtocol(st protocol.Status, mf func(p *radius.Packet) *radius.Packet) {
	ctx.log.Info("Ending protocol")
	if ctx.parent != nil {
		ctx.parent.EndInnerProtocol(st, mf)
		return
	}
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

func (ctx *context) callEndModifier(p *radius.Packet) *radius.Packet {
	if ctx.parent != nil {
		p = ctx.parent.callEndModifier(p)
	}
	if ctx.endModifier != nil {
		p = ctx.endModifier(p)
	}
	return p
}
