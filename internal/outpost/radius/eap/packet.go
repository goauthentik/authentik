package eap

import (
	"encoding/binary"
	"errors"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/tls"
)

type Code uint8

const (
	CodeRequest  Code = 1
	CodeResponse Code = 2
	CodeSuccess  Code = 3
)

type Type uint8

const (
	TypeIdentity     Type = 1
	TypeMD5Challenge Type = 4
	TypeTLS          Type = 13
)

type Packet struct {
	code       Code
	id         uint8
	length     uint16
	msgType    Type
	rawPayload []byte
	Payload    protocol.Payload
}

type PayloadWriter struct{}

func emptyPayload(t Type) protocol.Payload {
	switch t {
	case TypeIdentity:
		return &IdentityPayload{}
	case TypeTLS:
		return &tls.Payload{}
	}
	return nil
}

func Decode(raw []byte) (*Packet, error) {
	packet := &Packet{}
	packet.code = Code(raw[0])
	packet.id = raw[1]
	packet.length = binary.BigEndian.Uint16(raw[2:])
	if packet.length != uint16(len(raw)) {
		return nil, errors.New("mismatched packet length")
	}
	if len(raw) > 4 && (packet.code == CodeRequest || packet.code == CodeResponse) {
		packet.msgType = Type(raw[4])
	}
	packet.Payload = emptyPayload(packet.msgType)
	packet.rawPayload = raw[5:]
	log.WithField("raw", debug.FormatBytes(raw)).Debug("EAP: decode raw")
	err := packet.Payload.Decode(raw[5:])
	if err != nil {
		return nil, err
	}
	return packet, nil
}

func (p *Packet) Encode() ([]byte, error) {
	buff := make([]byte, 5)
	buff[0] = uint8(p.code)
	buff[1] = uint8(p.id)

	payloadBuffer, err := p.Payload.Encode()
	if err != nil {
		return buff, err
	}
	binary.BigEndian.PutUint16(buff[2:], uint16(len(payloadBuffer)+5))
	if p.code == CodeRequest || p.code == CodeResponse {
		buff[4] = uint8(p.msgType)
	}
	buff = append(buff, payloadBuffer...)
	return buff, nil
}
