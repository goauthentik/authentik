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
	res, newState := p.GetChallengeForType(st, nextChallengeToOffer)
	stm.SetEAPState(rst, newState)

	rres := r.Response(radius.CodeAccessChallenge)
	if _, ok := res.Payload.(protocol.EmptyPayload); ok {
		res.code = CodeSuccess
		rres.Code = radius.CodeAccessAccept
		res.id -= 1
		rfc2865.UserName_SetString(rres, "foo")
		rfc2865.FramedMTU_Set(rres, rfc2865.FramedMTU(1400))
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

func (p *Packet) GetChallengeForType(st *State, t Type) (*Packet, *State) {
	res := &Packet{
		code:    CodeRequest,
		id:      p.id + 1,
		msgType: t,
	}
	var payload any
	var tst any
	switch t {
	case TypeTLS:
		if _, ok := p.Payload.(*tls.Payload); !ok {
			p.Payload = &tls.Payload{}
			p.Payload.Decode(p.rawPayload)
		}
		payload, tst = p.Payload.(*tls.Payload).Handle(st.TypeState[t])
	}
	st.TypeState[t] = tst
	res.Payload = payload.(protocol.Payload)
	return res, st
}

func (p *Packet) setMessageAuthenticator(rp *radius.Packet) {
	err := rfc2869.MessageAuthenticator_Set(rp, make([]byte, 16))
	if err != nil {
		panic(err)
	}
	hash := hmac.New(md5.New, rp.Secret)
	encode, err := rp.MarshalBinary()
	if err != nil {
		panic(err)
	}
	hash.Write(encode)
	err = rfc2869.MessageAuthenticator_Set(rp, hash.Sum(nil))
	if err != nil {
		panic(err)
	}
}
