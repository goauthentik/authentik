package identity

import "goauthentik.io/internal/outpost/radius/eap/protocol"

const TypeIdentity protocol.Type = 1

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	Identity string
}

func (ip *Payload) Type() protocol.Type {
	return TypeIdentity
}

func (ip *Payload) Decode(raw []byte) error {
	ip.Identity = string(raw)
	return nil
}

func (ip *Payload) Encode() ([]byte, error) {
	return []byte{}, nil
}

func (ip *Payload) Handle(ctx protocol.Context) protocol.Payload {
	if ctx.IsProtocolStart() {
		ctx.EndInnerProtocol(protocol.StatusNextProtocol, nil)
	}
	return nil
}

func (ip *Payload) Offerable() bool {
	return false
}
