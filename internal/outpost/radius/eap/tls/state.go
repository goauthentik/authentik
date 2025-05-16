package tls

import (
	"context"
	"crypto/tls"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

type State struct {
	HasStarted       bool
	RemainingChunks  [][]byte
	HandshakeDone    bool
	FinalStatus      protocol.Status
	ClientHello      *tls.ClientHelloInfo
	MPPEKey          []byte
	TotalPayloadSize int
	TLS              *tls.Conn
	Conn             *BuffConn
	Context          context.Context
	ContextCancel    context.CancelFunc
}

func NewState(c protocol.Context) interface{} {
	c.Log().Debug("TLS: new state")
	return &State{
		RemainingChunks: make([][]byte, 0),
	}
}

func (s State) HasMore() bool {
	return len(s.RemainingChunks) > 0
}
