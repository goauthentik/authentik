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
}

func (p *Payload) Type() protocol.Type {
	return TypePEAP
}

func (p *Payload) Decode(raw []byte) error {
	log.WithField("raw", debug.FormatBytes(raw)).Debug("PEAP: Decode")
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	log.Debug("PEAP: Encode")
	return []byte{}, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	eapState := ctx.StateForProtocol(eap.TypeEAP).(*eap.State)
	if !ctx.IsProtocolStart() {
		ctx.Log().Debug("PEAP: Protocol start")
		return &eap.Payload{
			Code:    protocol.CodeRequest,
			ID:      eapState.PacketID,
			MsgType: identity.TypeIdentity,
			Payload: &identity.Payload{},
		}
	}
	return &Payload{}
}

func (p *Payload) Offerable() bool {
	return true
}
