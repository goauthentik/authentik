package eap

import (
	"encoding/binary"
	"fmt"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

const TypeEAP protocol.Type = 0

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	Code       protocol.Code
	ID         uint8
	Length     uint16
	MsgType    protocol.Type
	Payload    protocol.Payload
	RawPayload []byte
}

func (ip *Payload) Type() protocol.Type {
	return TypeEAP
}

func (ip *Payload) Offerable() bool {
	return false
}

func (packet *Payload) Decode(raw []byte) error {
	packet.Code = protocol.Code(raw[0])
	packet.ID = raw[1]
	packet.Length = binary.BigEndian.Uint16(raw[2:])
	if packet.Length != uint16(len(raw)) {
		return fmt.Errorf("mismatched packet length; got %d, expected %d", packet.Length, uint16(len(raw)))
	}
	if len(raw) > 4 && (packet.Code == protocol.CodeRequest || packet.Code == protocol.CodeResponse) {
		packet.MsgType = protocol.Type(raw[4])
	}
	log.WithField("raw", debug.FormatBytes(raw)).WithField("payload", fmt.Sprintf("%T", packet.Payload)).Trace("EAP: decode raw")
	packet.RawPayload = raw[5:]
	if packet.Payload == nil {
		return nil
	}
	err := packet.Payload.Decode(raw[5:])
	if err != nil {
		return err
	}
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	buff := make([]byte, 4)
	buff[0] = uint8(p.Code)
	buff[1] = uint8(p.ID)

	if p.Payload != nil {
		payloadBuffer, err := p.Payload.Encode()
		if err != nil {
			return buff, err
		}
		if p.Code == protocol.CodeRequest || p.Code == protocol.CodeResponse {
			buff = append(buff, uint8(p.MsgType))
		}
		buff = append(buff, payloadBuffer...)
	}
	binary.BigEndian.PutUint16(buff[2:], uint16(len(buff)))
	return buff, nil
}

func (ip *Payload) Handle(ctx protocol.Context) protocol.Payload {
	ctx.Log().Debug("EAP: Handle")
	return nil
}
