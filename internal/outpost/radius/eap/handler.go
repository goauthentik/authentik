package eap

import (
	"crypto/hmac"
	"crypto/md5"
	"encoding/base64"
	"fmt"

	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/legacy_nak"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/rfc2869"
)

func sendErrorResponse(w radius.ResponseWriter, r *radius.Request) {
	rres := r.Response(radius.CodeAccessReject)
	err := w.Write(rres)
	if err != nil {
		log.WithError(err).Warning("failed to send response")
	}
}

func (p *Packet) HandleRadiusPacket(w radius.ResponseWriter, r *radius.Request) {
	rst := rfc2865.State_GetString(r.Packet)
	if rst == "" {
		rst = base64.StdEncoding.EncodeToString(securecookie.GenerateRandomKey(12))
	}
	p.state = rst

	rp, err := p.handleInner(r)
	rres := r.Response(radius.CodeAccessReject)
	if err == nil {
		rres = p.endModifier(rres)
		switch rp.code {
		case CodeRequest:
			rres.Code = radius.CodeAccessChallenge
		case CodeFailure:
			rres.Code = radius.CodeAccessReject
		case CodeSuccess:
			rres.Code = radius.CodeAccessAccept
		}
	} else {
		rres.Code = radius.CodeAccessReject
		log.WithError(err).Debug("Rejecting request")
	}

	rfc2865.State_SetString(rres, p.state)
	eapEncoded, err := rp.Encode()
	if err != nil {
		log.WithError(err).Warning("failed to encode response")
		sendErrorResponse(w, r)
		return
	}
	log.WithField("length", len(eapEncoded)).WithField("type", fmt.Sprintf("%T", rp.Payload)).Debug("EAP: encapsulated challenge")
	rfc2869.EAPMessage_Set(rres, eapEncoded)
	err = p.setMessageAuthenticator(rres)
	if err != nil {
		log.WithError(err).Warning("failed to send message authenticator")
		sendErrorResponse(w, r)
		return
	}
	err = w.Write(rres)
	if err != nil {
		log.WithError(err).Warning("failed to send response")
	}
}

func (p *Packet) handleInner(r *radius.Request) (*Packet, error) {
	st := p.stm.GetEAPState(p.state)
	if st == nil {
		log.Debug("EAP: blank state")
		st = BlankState(p.stm.GetEAPSettings())
	}

	nextChallengeToOffer, err := st.GetNextProtocol()
	if err != nil {
		return &Packet{
			code: CodeFailure,
			id:   p.id,
		}, err
	}

	next := func() (*Packet, error) {
		st.ProtocolIndex += 1
		p.stm.SetEAPState(p.state, st)
		return p.handleInner(r)
	}

	if _, ok := p.Payload.(*legacy_nak.Payload); ok {
		log.Debug("EAP: received NAK, trying next protocol")
		p.Payload = nil
		return next()
	}

	np, _ := emptyPayload(p.stm, nextChallengeToOffer)

	ctx := &context{
		req:      r,
		state:    st.TypeState[np.Type()],
		log:      log.WithField("type", fmt.Sprintf("%T", np)),
		settings: p.stm.GetEAPSettings().ProtocolSettings[np.Type()],
	}
	if !np.Offerable() {
		ctx.log.Debug("EAP: protocol not offerable, skipping")
		return next()
	}
	ctx.log.Debug("EAP: Passing to protocol")

	res := p.GetChallengeForType(ctx, np)
	st.TypeState[np.Type()] = ctx.GetProtocolState()
	p.stm.SetEAPState(p.state, st)

	if ctx.endModifier != nil {
		p.endModifier = ctx.endModifier
	}

	switch ctx.endStatus {
	case protocol.StatusSuccess:
		res.code = CodeSuccess
		res.id -= 1
	case protocol.StatusError:
		res.code = CodeFailure
		res.id -= 1
	case protocol.StatusNextProtocol:
		ctx.log.Debug("EAP: Protocol ended, starting next protocol")
		return next()
	case protocol.StatusUnknown:
	}
	return res, nil
}

func (p *Packet) GetChallengeForType(ctx *context, np protocol.Payload) *Packet {
	res := &Packet{
		code:    CodeRequest,
		id:      p.id + 1,
		msgType: np.Type(),
	}
	var payload any
	if ctx.IsProtocolStart() {
		p.Payload = np
		p.Payload.Decode(p.rawPayload)
	}
	payload = p.Payload.Handle(ctx)
	if payload != nil {
		res.Payload = payload.(protocol.Payload)
	}
	return res
}

func (p *Packet) setMessageAuthenticator(rp *radius.Packet) error {
	_ = rfc2869.MessageAuthenticator_Set(rp, make([]byte, 16))
	hash := hmac.New(md5.New, rp.Secret)
	encode, err := rp.MarshalBinary()
	if err != nil {
		return err
	}
	hash.Write(encode)
	_ = rfc2869.MessageAuthenticator_Set(rp, hash.Sum(nil))
	return nil
}
