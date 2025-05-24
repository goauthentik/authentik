package mschapv2

import (
	"layeh.com/radius/rfc2759"
	"layeh.com/radius/rfc3079"
)

type Settings struct {
	AuthenticateRequest func(req AuthRequest) (*AuthResponse, error)
}

type AuthRequest struct {
	Challenge     []byte
	PeerChallenge []byte
}

type AuthResponse struct {
	NTResponse            []byte
	RecvKey               []byte
	SendKey               []byte
	AuthenticatorResponse string
}

func DebugStaticCredentials(user, password []byte) func(req AuthRequest) (*AuthResponse, error) {
	return func(req AuthRequest) (*AuthResponse, error) {
		res := &AuthResponse{}
		ntResponse, err := rfc2759.GenerateNTResponse(req.Challenge, req.PeerChallenge, user, password)
		if err != nil {
			return nil, err
		}
		res.NTResponse = ntResponse

		res.RecvKey, err = rfc3079.MakeKey(ntResponse, password, false)
		if err != nil {
			return nil, err
		}

		res.SendKey, err = rfc3079.MakeKey(ntResponse, password, true)
		if err != nil {
			return nil, err
		}

		res.AuthenticatorResponse, err = rfc2759.GenerateAuthenticatorResponse(req.Challenge, req.PeerChallenge, ntResponse, user, password)
		if err != nil {
			return nil, err
		}
		return res, nil

	}
}
