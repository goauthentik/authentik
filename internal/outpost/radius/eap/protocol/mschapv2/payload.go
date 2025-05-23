package mschapv2

import (
	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

const TypeMSCHAPv2 protocol.Type = 26

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
}

func (p *Payload) Type() protocol.Type {
	return TypeMSCHAPv2
}

func (p *Payload) Decode(raw []byte) error {
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	return []byte{}, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	if ctx.IsProtocolStart(TypeMSCHAPv2) {
		ctx.EndInnerProtocol(protocol.StatusError, nil)
	}
	return nil
}

func (p *Payload) Offerable() bool {
	return true
}

func (p *Payload) String() string {
	return "<MSCHAPv2 Packet >"
}
