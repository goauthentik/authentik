package mschapv2

type State struct {
	Challenge       []byte
	PeerChallenge   []byte
	Authenticated   bool
	IsProtocolEnded bool
	recvKey         []byte
	sendKey         []byte
}
