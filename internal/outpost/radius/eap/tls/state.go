package tls

import (
	"context"
	"crypto/tls"
)

type State struct {
	HasStarted       bool
	RemainingChunks  [][]byte
	HandshakeDone    bool
	ClientHello      *tls.ClientHelloInfo
	MPPEKey          []byte
	TotalPayloadSize int
	TLS              *tls.Conn
	Conn             *BuffConn
	Context          context.Context
	ContextCancel    context.CancelFunc
}

func NewState() *State {
	return &State{
		RemainingChunks: make([][]byte, 0),
	}
}

func (s State) HasMore() bool {
	return len(s.RemainingChunks) > 0
}
