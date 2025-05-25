package gtc

import (
	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

const TypeGTC protocol.Type = 6

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	Challenge []byte

	st  *State
	raw []byte
}

func (p *Payload) Type() protocol.Type {
	return TypeGTC
}

func (p *Payload) Decode(raw []byte) error {
	p.raw = raw
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	return p.Challenge, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	defer func() {
		ctx.SetProtocolState(TypeGTC, p.st)
	}()
	settings := ctx.ProtocolSettings().(Settings)
	if ctx.IsProtocolStart(TypeGTC) {
		g, v := settings.ChallengeHandler(ctx)
		p.st = &State{
			getChallenge:     g,
			validateResponse: v,
		}
		return &Payload{
			Challenge: p.st.getChallenge(),
		}
	}
	p.st = ctx.GetProtocolState(TypeGTC).(*State)
	p.st.validateResponse(p.raw)
	return &Payload{
		Challenge: p.st.getChallenge(),
	}
}

func (p *Payload) Offerable() bool {
	return true
}

func (p *Payload) String() string {
	return "<GTC Packet>"
}
