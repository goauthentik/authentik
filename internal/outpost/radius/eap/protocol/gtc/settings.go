package gtc

import "goauthentik.io/internal/outpost/radius/eap/protocol"

type GetChallenge func() []byte
type ValidateResponse func(answer []byte)

type Settings struct {
	ChallengeHandler func(ctx protocol.Context) (GetChallenge, ValidateResponse)
}
