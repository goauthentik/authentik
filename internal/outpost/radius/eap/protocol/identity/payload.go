package identity

import "goauthentik.io/internal/outpost/radius/eap/protocol"

const TypeIdentity protocol.Type = 1

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	Identity string
}

func (p *Payload) Type() protocol.Type {
	return TypeIdentity
}

func (p *Payload) Decode(raw []byte) error {
	p.Identity = string(raw)
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	return []byte{}, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	if ctx.IsProtocolStart(TypeIdentity) {
		ctx.EndInnerProtocol(protocol.StatusNextProtocol, nil)
	}
	return nil
}

func (p *Payload) Offerable() bool {
	return false
}
