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

	Settings protocol.Settings
}

func (p *Payload) Type() protocol.Type {
	return TypeEAP
}

func (p *Payload) Offerable() bool {
	return false
}

func (p *Payload) Decode(raw []byte) error {
	p.Code = protocol.Code(raw[0])
	p.ID = raw[1]
	p.Length = binary.BigEndian.Uint16(raw[2:])
	if p.Length != uint16(len(raw)) {
		return fmt.Errorf("mismatched packet length; got %d, expected %d", p.Length, uint16(len(raw)))
	}
	if len(raw) > 4 && (p.Code == protocol.CodeRequest || p.Code == protocol.CodeResponse) {
		p.MsgType = protocol.Type(raw[4])
	}
	log.WithField("raw", debug.FormatBytes(raw)).Trace("EAP: decode raw")
	p.RawPayload = raw[5:]
	pp, _, err := EmptyPayload(p.Settings, p.MsgType)
	if err != nil {
		return err
	}
	p.Payload = pp
	err = p.Payload.Decode(raw[5:])
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

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	ctx.Log().Debug("EAP: Handle")
	return nil
}

func (p *Payload) String() string {
	return fmt.Sprintf(
		"<EAP Packet Code=%d, ID=%d, Type=%d, Length=%d, Payload=%T>",
		p.Code,
		p.ID,
		p.MsgType,
		p.Length,
		p.Payload,
	)
}
