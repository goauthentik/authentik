package mschapv2

import (
	"bytes"
	"errors"

	"layeh.com/radius/rfc2759"
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
	authenticatorResponse, err := rfc2759.GenerateAuthenticatorResponse(p.st.Challenge, p.st.PeerChallenge, ntResponse, byteUser, bytePwd)
	if err != nil {
		return nil, err
	}
	return []byte(authenticatorResponse), nil
}
