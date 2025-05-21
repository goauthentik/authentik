package legacy_nak

import "goauthentik.io/internal/outpost/radius/eap/protocol"

const TypeLegacyNAK protocol.Type = 3

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	DesiredType protocol.Type
}

func (ln *Payload) Type() protocol.Type {
	return TypeLegacyNAK
}

func (ln *Payload) Decode(raw []byte) error {
	ln.DesiredType = protocol.Type(raw[0])
	return nil
}

func (ln *Payload) Encode() ([]byte, error) {
	return []byte{byte(ln.DesiredType)}, nil
}

func (ln *Payload) Handle(ctx protocol.Context) protocol.Payload {
	if ctx.IsProtocolStart(TypeLegacyNAK) {
		ctx.EndInnerProtocol(protocol.StatusError, nil)
	}
	return nil
}

func (ln *Payload) Offerable() bool {
	return false
}
