package peap

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/tls"
)

const TypePEAP protocol.Type = 25

func Protocol() protocol.Payload {
	return &tls.Payload{
		Inner: &Payload{},
	}
}

type Payload struct {
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
	log.Debug("PEAP: Handle")
	return &Payload{}
}

func (p *Payload) Offerable() bool {
	return true
}
