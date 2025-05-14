package tls

import (
	"context"
	"crypto/tls"
)

type State struct {
	HasStarted       bool
	RemainingChunks  [][]byte
	TotalPayloadSize int
	TLS              *tls.Conn
	Conn             *TLSConnection
	Context          context.Context
}

func NewState() *State {
	return &State{
		RemainingChunks: make([][]byte, 0),
	}
}

func (s State) HasMore() bool {
	return len(s.RemainingChunks) > 0
}
