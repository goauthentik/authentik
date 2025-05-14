package tls

import "crypto/tls"

type State struct {
	HasStarted      bool
	RemainingChunks [][]byte
	TLS             *tls.Conn
}

func NewState() State {
	return State{
		RemainingChunks: make([][]byte, 0),
	}
}

func (s State) HasMore() bool {
	return len(s.RemainingChunks) > 0
}
