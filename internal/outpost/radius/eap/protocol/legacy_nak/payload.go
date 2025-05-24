package legacy_nak

import (
	"fmt"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

const TypeLegacyNAK protocol.Type = 3

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	DesiredType protocol.Type
}

func (p *Payload) Type() protocol.Type {
	return TypeLegacyNAK
}

func (p *Payload) Decode(raw []byte) error {
	p.DesiredType = protocol.Type(raw[0])
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	return []byte{byte(p.DesiredType)}, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	if ctx.IsProtocolStart(TypeLegacyNAK) {
		ctx.EndInnerProtocol(protocol.StatusError)
	}
	return nil
}

func (p *Payload) Offerable() bool {
	return false
}

func (p *Payload) String() string {
	return fmt.Sprintf(
		"<Legacy NAK Packet DesiredType=%d>",
		p.DesiredType,
	)
}
