package eap

import (
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/eap"
	"layeh.com/radius"
)

type Packet struct {
	r           *radius.Request
	eap         *eap.Payload
	stm         protocol.StateManager
	state       string
	endModifier func(p *radius.Packet) *radius.Packet
}

func Decode(stm protocol.StateManager, raw []byte) (*Packet, error) {
	packet := &Packet{
		eap: &eap.Payload{
			Settings: stm.GetEAPSettings(),
		},
		stm: stm,
		endModifier: func(p *radius.Packet) *radius.Packet {
			return p
		},
	}
	err := packet.eap.Decode(raw)
	if err != nil {
		return nil, err
	}
	return packet, nil
}

func (p *Packet) Encode() ([]byte, error) {
	return p.eap.Encode()
}
