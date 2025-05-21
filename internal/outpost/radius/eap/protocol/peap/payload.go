package peap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/eap"
	"goauthentik.io/internal/outpost/radius/eap/protocol/identity"
	"goauthentik.io/internal/outpost/radius/eap/protocol/tls"
)

const TypePEAP protocol.Type = 25

func Protocol() protocol.Payload {
	return &tls.Payload{
		Inner: &Payload{
			Inner: &eap.Payload{},
		},
	}
}

type Payload struct {
	Inner protocol.Payload

	eap *eap.Payload
	st  *State
	raw []byte
}

func (p *Payload) Type() protocol.Type {
	return TypePEAP
}

func (p *Payload) HasInner() protocol.Payload {
	return p.Inner
}

func (p *Payload) Decode(raw []byte) error {
	log.WithField("raw", debug.FormatBytes(raw)).Debug("PEAP: Decode")
	p.raw = raw
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	return p.eap.Encode()
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	defer func() {
		ctx.SetProtocolState(TypePEAP, p.st)
	}()

	rootEap := ctx.RootPayload().(*eap.Payload)

	if ctx.IsProtocolStart(TypePEAP) {
		ctx.Log().Debug("PEAP: Protocol start")
		p.st = &State{}
		return &eap.Payload{
			Code:    protocol.CodeRequest,
			ID:      rootEap.ID + 1,
			MsgType: identity.TypeIdentity,
			Payload: &identity.Payload{},
		}
	}
	p.st = ctx.GetProtocolState(TypePEAP).(*State)

	ep := &eap.Payload{}
	err := ep.Decode(p.raw)
	if err != nil {
		ctx.Log().WithError(err).Warning("PEAP: failed to decode inner EAP")
		return &Payload{}
	}
	return &Payload{}
}

func (p *Payload) Offerable() bool {
	return true
}
