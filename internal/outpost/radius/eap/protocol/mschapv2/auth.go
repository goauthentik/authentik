package mschapv2

import (
	"bytes"
	"errors"

	"layeh.com/radius/rfc2759"
	"layeh.com/radius/rfc3079"
)

func (p *Payload) checkChapPassword(res *Response) ([]byte, error) {
	byteUser := []byte("foo")
	bytePwd := []byte("bar")
	ntResponse, err := rfc2759.GenerateNTResponse(p.st.Challenge, p.st.PeerChallenge, byteUser, bytePwd)
	if err != nil {
		return nil, err
	}

	if !bytes.Equal(ntResponse, res.NTResponse) {
		return nil, errors.New("nt response mismatch")
	}

	p.st.recvKey, err = rfc3079.MakeKey(ntResponse, bytePwd, false)
	if err != nil {
		return nil, err
	}

	p.st.sendKey, err = rfc3079.MakeKey(ntResponse, bytePwd, true)
	if err != nil {
		return nil, err
	}

	authenticatorResponse, err := rfc2759.GenerateAuthenticatorResponse(p.st.Challenge, p.st.PeerChallenge, ntResponse, byteUser, bytePwd)
	if err != nil {
		return nil, err
	}
	return []byte(authenticatorResponse), nil
}
