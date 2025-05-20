package eap

import (
	"encoding/binary"
	"errors"
	"fmt"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
)

type Code uint8

const (
	CodeRequest  Code = 1
	CodeResponse Code = 2
	CodeSuccess  Code = 3
	CodeFailure  Code = 4
)

type Packet struct {
	code       Code
	id         uint8
	length     uint16
	msgType    protocol.Type
	rawPayload []byte
	Payload    protocol.Payload

	stm         StateManager
	state       string
	endModifier func(p *radius.Packet) *radius.Packet
}

type PayloadWriter struct{}

func emptyPayload(stm StateManager, t protocol.Type) (protocol.Payload, error) {
	for _, cons := range stm.GetEAPSettings().Protocols {
		if np := cons(); np.Type() == t {
			return np, nil
		}
	}
	return nil, fmt.Errorf("unsupported EAP type %d", t)
}

func Decode(stm StateManager, raw []byte) (*Packet, error) {
	packet := &Packet{
		stm: stm,
		endModifier: func(p *radius.Packet) *radius.Packet {
			return p
		},
	}
	packet.code = Code(raw[0])
	packet.id = raw[1]
	packet.length = binary.BigEndian.Uint16(raw[2:])
	if packet.length != uint16(len(raw)) {
		return nil, errors.New("mismatched packet length")
	}
	if len(raw) > 4 && (packet.code == CodeRequest || packet.code == CodeResponse) {
		packet.msgType = protocol.Type(raw[4])
	}
	p, err := emptyPayload(stm, packet.msgType)
	if err != nil {
		return nil, err
	}
	packet.Payload = p
	packet.rawPayload = raw[5:]
	log.WithField("raw", debug.FormatBytes(raw)).WithField("payload", fmt.Sprintf("%T", packet.Payload)).Debug("EAP: decode raw")
	err = packet.Payload.Decode(raw[5:])
	if err != nil {
		return nil, err
	}
	return packet, nil
}

func (p *Packet) Encode() ([]byte, error) {
	buff := make([]byte, 4)
	buff[0] = uint8(p.code)
	buff[1] = uint8(p.id)

	if p.Payload != nil {
		payloadBuffer, err := p.Payload.Encode()
		if err != nil {
			return buff, err
		}
		if p.code == CodeRequest || p.code == CodeResponse {
			buff = append(buff, uint8(p.msgType))
		}
		buff = append(buff, payloadBuffer...)
	}
	binary.BigEndian.PutUint16(buff[2:], uint16(len(buff)))
	return buff, nil
}
