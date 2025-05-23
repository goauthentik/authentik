package eap

import (
	"crypto/hmac"
	"crypto/md5"
	"encoding/base64"
	"fmt"

	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/eap"
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

	rep, err := p.handleInner(r)
	rp := &Packet{
		eap: rep,
	}

	rres := r.Response(radius.CodeAccessReject)
	if err == nil {
		rres = p.endModifier(rres)
		switch rp.eap.Code {
		case protocol.CodeRequest:
			rres.Code = radius.CodeAccessChallenge
		case protocol.CodeFailure:
			rres.Code = radius.CodeAccessReject
		case protocol.CodeSuccess:
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
	log.WithField("length", len(eapEncoded)).WithField("type", fmt.Sprintf("%T", rp.eap.Payload)).Debug("Root-EAP: encapsulated challenge")
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

func (p *Packet) handleInner(r *radius.Request) (*eap.Payload, error) {
	st := p.stm.GetEAPState(p.state)
	if st == nil {
		log.Debug("Root-EAP: blank state")
		st = protocol.BlankState(p.stm.GetEAPSettings())
	}

	nextChallengeToOffer, err := st.GetNextProtocol()
	if err != nil {
		return &eap.Payload{
			Code: protocol.CodeFailure,
			ID:   p.eap.ID,
		}, err
	}

	next := func() (*eap.Payload, error) {
		st.ProtocolIndex += 1
		st.TypeState = map[protocol.Type]any{}
		p.stm.SetEAPState(p.state, st)
		return p.handleInner(r)
	}

	if _, ok := p.eap.Payload.(*legacy_nak.Payload); ok {
		log.Debug("Root-EAP: received NAK, trying next protocol")
		p.eap.Payload = nil
		return next()
	}

	np, t, _ := emptyPayload(p.stm, nextChallengeToOffer)

	ctx := &context{
		req:         r,
		rootPayload: p.eap,
		typeState:   st.TypeState,
		log:         log.WithField("type", fmt.Sprintf("%T", np)).WithField("code", t),
		settings:    p.stm.GetEAPSettings().ProtocolSettings[t],
	}
	if !np.Offerable() {
		ctx.log.Debug("Root-EAP: protocol not offerable, skipping")
		return next()
	}
	ctx.log.Debug("Root-EAP: Passing to protocol")

	res := p.GetChallengeForType(ctx, np, t)
	p.stm.SetEAPState(p.state, st)

	if ctx.endModifier != nil {
		p.endModifier = ctx.endModifier
	}

	switch ctx.endStatus {
	case protocol.StatusSuccess:
		res.Code = protocol.CodeSuccess
		res.ID -= 1
	case protocol.StatusError:
		res.Code = protocol.CodeFailure
		res.ID -= 1
	case protocol.StatusNextProtocol:
		ctx.log.Debug("Root-EAP: Protocol ended, starting next protocol")
		return next()
	case protocol.StatusUnknown:
	}
	return res, nil
}

func (p *Packet) GetChallengeForType(ctx *context, np protocol.Payload, t protocol.Type) *eap.Payload {
	res := &eap.Payload{
		Code:    protocol.CodeRequest,
		ID:      p.eap.ID + 1,
		MsgType: t,
	}
	var payload any
	if ctx.IsProtocolStart(t) {
		p.eap.Payload = np
		p.eap.Payload.Decode(p.eap.RawPayload)
	}
	payload = p.eap.Payload.Handle(ctx)
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
