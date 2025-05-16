package eap

import (
	"crypto/hmac"
	"crypto/md5"
	"encoding/base64"

	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/tls"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/rfc2869"
)

func (p *Packet) Handle(stm StateManager, w radius.ResponseWriter, r *radius.Packet) {
	rst := rfc2865.State_GetString(r)
	if rst == "" {
		rst = base64.StdEncoding.EncodeToString(securecookie.GenerateRandomKey(12))
	}
	st := stm.GetEAPState(rst)
	if st == nil {
		log.Debug("EAP: blank state")
		st = BlankState(stm.GetEAPSettings())
	}
	if len(st.ChallengesToOffer) < 1 {
		panic("No more challenges")
	}
	nextChallengeToOffer := st.ChallengesToOffer[0]

	ctx := &context{
		state:    st.TypeState[nextChallengeToOffer],
		log:      log.WithField("type", nextChallengeToOffer),
		settings: stm.GetEAPSettings().ProtocolSettings[nextChallengeToOffer],
	}

	res := p.GetChallengeForType(ctx, nextChallengeToOffer)
	st.TypeState[nextChallengeToOffer] = ctx.GetProtocolState(nil)
	stm.SetEAPState(rst, st)

	rres := r.Response(radius.CodeAccessChallenge)
	switch ctx.endStatus {
	case protocol.StatusSuccess:
		res.code = CodeSuccess
		res.id -= 1
		rres = ctx.endModifier(rres)
		st.ChallengesToOffer = st.ChallengesToOffer[1:]
		if len(st.ChallengesToOffer) < 1 {
			rres.Code = radius.CodeAccessAccept
		}
	case protocol.StatusError:
		res.code = CodeFailure
		res.id -= 1
		st.ChallengesToOffer = st.ChallengesToOffer[1:]
		rres = ctx.endModifier(rres)
		if len(st.ChallengesToOffer) < 1 {
			rres.Code = radius.CodeAccessReject
		}
	case protocol.StatusUnknown:
	}
	rfc2865.State_SetString(rres, rst)
	eapEncoded, err := res.Encode()
	if err != nil {
		panic(err)
	}
	log.WithField("length", len(eapEncoded)).Debug("EAP: encapsulating challenge")
	rfc2869.EAPMessage_Set(rres, eapEncoded)
	p.setMessageAuthenticator(rres)
	err = w.Write(rres)
	if err != nil {
		panic(err)
	}
}

func (p *Packet) GetChallengeForType(ctx *context, t protocol.Type) *Packet {
	res := &Packet{
		code:    CodeRequest,
		id:      p.id + 1,
		msgType: t,
	}
	var payload any
	switch t {
	case tls.TypeTLS:
		if _, ok := p.Payload.(*tls.Payload); !ok {
			p.Payload = &tls.Payload{}
			p.Payload.Decode(p.rawPayload)
		}
		payload = p.Payload.(*tls.Payload).Handle(ctx)
	}
	if payload != nil {
		res.Payload = payload.(protocol.Payload)
	}
	return res
}

func (p *Packet) setMessageAuthenticator(rp *radius.Packet) {
	_ = rfc2869.MessageAuthenticator_Set(rp, make([]byte, 16))
	hash := hmac.New(md5.New, rp.Secret)
	encode, err := rp.MarshalBinary()
	if err != nil {
		panic(err)
	}
	hash.Write(encode)
	_ = rfc2869.MessageAuthenticator_Set(rp, hash.Sum(nil))
}
