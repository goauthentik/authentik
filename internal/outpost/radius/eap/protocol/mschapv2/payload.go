package mschapv2

import (
	"encoding/binary"
	"fmt"

	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/eap"
	"goauthentik.io/internal/outpost/radius/eap/protocol/peap"
)

const TypeMSCHAPv2 protocol.Type = 26

func Protocol() protocol.Payload {
	return &Payload{}
}

const (
	challengeValueSize     = 16
	responseValueSize      = 49
	responseReservedSize   = 8
	responseNTResponseSize = 24
)

type OpCode uint8

const (
	OpChallenge OpCode = 1
	OpResponse  OpCode = 2
	OpSuccess   OpCode = 3
)

type Payload struct {
	OpCode     OpCode
	MSCHAPv2ID uint8
	MSLength   uint16
	ValueSize  uint8

	Challenge []byte
	Response  []byte

	Name []byte

	st *State
}

func (p *Payload) Type() protocol.Type {
	return TypeMSCHAPv2
}

func (p *Payload) Decode(raw []byte) error {
	log.WithField("raw", debug.FormatBytes(raw)).Debugf("MSCHAPv2: decode raw")
	p.OpCode = OpCode(raw[0])
	if p.OpCode == OpSuccess {
		return nil
	}
	// TODO: Validate against root EAP packet
	p.MSCHAPv2ID = raw[1]
	p.MSLength = binary.BigEndian.Uint16(raw[2:])

	p.ValueSize = raw[4]
	if p.ValueSize != responseValueSize {
		return fmt.Errorf("mschapv2: incorrect value size: %d", p.ValueSize)
	}
	p.Response = raw[5 : p.ValueSize+5]
	p.Name = raw[5+p.ValueSize:]
	if int(p.MSLength) != len(raw) {
		return fmt.Errorf("MSCHAPv2: incorrect MS-Length: %d, should be %d", p.MSLength, len(raw))
	}
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	encoded := []byte{
		byte(p.OpCode),
		p.MSCHAPv2ID,
		0,
		0,
		byte(len(p.Challenge)),
	}
	encoded = append(encoded, p.Challenge...)
	encoded = append(encoded, p.Name...)
	p.MSLength = uint16(len(encoded))
	binary.BigEndian.PutUint16(encoded[2:], p.MSLength)
	return encoded, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	defer func() {
		ctx.SetProtocolState(TypeMSCHAPv2, p.st)
	}()

	rootEap := ctx.RootPayload().(*eap.Payload)

	if ctx.IsProtocolStart(TypeMSCHAPv2) {
		ctx.Log().Debug("MSCHAPv2: Empty state, starting")
		p.st = &State{
			Challenge: securecookie.GenerateRandomKey(challengeValueSize),
		}
		return &Payload{
			OpCode:     OpChallenge,
			MSCHAPv2ID: rootEap.ID + 1,
			Challenge:  p.st.Challenge,
			Name:       []byte("authentik"),
		}
	}
	p.st = ctx.GetProtocolState(TypeMSCHAPv2).(*State)

	response := &Payload{
		MSCHAPv2ID: rootEap.ID + 1,
	}

	ctx.Log().Debugf("MSCHAPv2: OpCode: %d", p.OpCode)
	if p.OpCode == OpResponse {
		res, err := ParseResponse(p.Response)
		if err != nil {
			ctx.Log().WithError(err).Warning("MSCHAPv2: failed to parse response")
			return nil
		}
		p.st.PeerChallenge = res.Challenge
		auth, err := p.checkChapPassword(res)
		if err != nil {
			ctx.Log().WithError(err).Warning("MSCHAPv2: failed to check password")
			return nil
		}
		ctx.Log().Info("MSCHAPv2: Successfully checked password")
		p.st.Authenticated = true
		succ := &SuccessRequest{
			Payload: &Payload{
				OpCode: OpSuccess,
			},
			Authenticator: auth,
		}
		return succ
	} else if p.OpCode == OpSuccess && p.st.Authenticated {
		return &peap.ExtensionPayload{
			AVPs: []peap.ExtensionAVP{
				{
					Mandatory: true,
					Type:      peap.AVPAckResult,
					Value:     []byte{0, 1},
				},
			},
		}
	}
	return response
}

func (p *Payload) Offerable() bool {
	return true
}

func (p *Payload) String() string {
	return fmt.Sprintf(
		"<MSCHAPv2 Packet OpCode=%d, MSCHAPv2ID=%d>",
		p.OpCode,
		p.MSCHAPv2ID,
	)
}
