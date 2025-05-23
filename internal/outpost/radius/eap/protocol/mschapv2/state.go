package mschapv2

type State struct {
	Challenge     []byte
	PeerChallenge []byte
}
