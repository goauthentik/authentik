package peap

import (
	"encoding/binary"
	"fmt"

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

	eap      *eap.Payload
	st       *State
	settings Settings
	raw      []byte
}

func (p *Payload) Type() protocol.Type {
	return TypePEAP
}

func (p *Payload) HasInner() protocol.Payload {
	return p.Inner
}

func (p *Payload) Decode(raw []byte) error {
	log.WithField("raw", debug.FormatBytes(raw)).Debug("PEAP: Decode")
	p.raw = raw
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	log.Debug("PEAP: Encode")
	return p.eap.Encode()
}

// Inner EAP packets in PEAP may not include the header, hence we need a custom decoder
// https://datatracker.ietf.org/doc/html/draft-kamath-pppext-peapv0-00.txt#section-1.1
func (p *Payload) eapInnerDecode(ctx protocol.Context) (*eap.Payload, error) {
	ep := &eap.Payload{
		Settings: p.GetEAPSettings(),
	}
	rootEap := ctx.RootPayload().(*eap.Payload)
	fixedRaw := []byte{
		byte(rootEap.Code),
		rootEap.ID,
		// 2 byte space for length
		0,
		0,
	}
	fullLength := len(p.raw) + len(fixedRaw)
	binary.BigEndian.PutUint16(fixedRaw[2:], uint16(fullLength))
	fixedRaw = append(fixedRaw, p.raw...)
	err := ep.Decode(fixedRaw)
	if err != nil {
		return nil, err
	}
	return ep, nil
}

func (p *Payload) eapEncodeInner(ctx protocol.Context) ([]byte, error) {
	return []byte{}, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	defer func() {
		ctx.SetProtocolState(TypePEAP, p.st)
	}()
	p.settings = ctx.ProtocolSettings().(Settings)

	rootEap := ctx.RootPayload().(*eap.Payload)

	if ctx.IsProtocolStart(TypePEAP) {
		ctx.Log().Debug("PEAP: Protocol start")
		p.st = &State{
			SubState: make(map[string]*protocol.State),
		}
		return &eap.Payload{
			Code:    protocol.CodeRequest,
			ID:      rootEap.ID + 1,
			MsgType: identity.TypeIdentity,
			Payload: &identity.Payload{},
		}
	}
	p.st = ctx.GetProtocolState(TypePEAP).(*State)

	ep, err := p.eapInnerDecode(ctx)
	if err != nil {
		ctx.Log().WithError(err).Warning("PEAP: failed to decode inner EAP")
		return &eap.Payload{
			Code: protocol.CodeFailure,
			ID:   rootEap.ID + 1,
		}
	}
	p.eap = ep
	ctx.Log().Debugf("PEAP: Decoded inner EAP to %s", ep.String())

	res, err := ctx.HandleInnerEAP(ep, p)
	if err != nil {
		ctx.Log().WithError(err).Warning("PEAP: failed to handle inner EAP")
	}
	return res
}

func (p *Payload) GetEAPSettings() protocol.Settings {
	return p.settings.InnerProtocols
}

func (p *Payload) GetEAPState(key string) *protocol.State {
	return p.st.SubState[key]
}

func (p *Payload) SetEAPState(key string, st *protocol.State) {
	p.st.SubState[key] = st
}

func (p *Payload) Offerable() bool {
	return true
}

func (p *Payload) String() string {
	return fmt.Sprintf(
		"<PEAP Packet Wrapping=%s>",
		p.eap.String(),
	)
}
