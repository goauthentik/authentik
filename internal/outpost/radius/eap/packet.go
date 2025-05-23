package eap

import (
	"fmt"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/eap"
	"layeh.com/radius"
)

type Packet struct {
	eap         *eap.Payload
	stm         protocol.StateManager
	state       string
	endModifier func(p *radius.Packet) *radius.Packet
}

func emptyPayload(stm protocol.StateManager, t protocol.Type) (protocol.Payload, protocol.Type, error) {
	for _, cons := range stm.GetEAPSettings().Protocols {
		np := cons()
		if np.Type() == t {
			return np, np.Type(), nil
		}
		// If the protocol has an inner protocol, return the original type but the code for the inner protocol
		if i, ok := np.(protocol.Inner); ok {
			if ii := i.HasInner(); ii != nil {
				return np, ii.Type(), nil
			}
		}
	}
	return nil, protocol.Type(0), fmt.Errorf("unsupported EAP type %d", t)
}

func Decode(stm protocol.StateManager, raw []byte) (*Packet, error) {
	packet := &Packet{
		eap: &eap.Payload{},
		stm: stm,
		endModifier: func(p *radius.Packet) *radius.Packet {
			return p
		},
	}
	// FIXME: We're decoding twice here, first to get the msg type, then come back to assign the payload type
	// then re-parse to parse the payload correctly
	err := packet.eap.Decode(raw)
	if err != nil {
		return nil, err
	}
	p, _, err := emptyPayload(stm, packet.eap.MsgType)
	if err != nil {
		return nil, err
	}
	packet.eap.Payload = p
	err = packet.eap.Decode(raw)
	if err != nil {
		return nil, err
	}
	return packet, nil
}

func (p *Packet) Encode() ([]byte, error) {
	return p.eap.Encode()
}
