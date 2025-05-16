package protocol

import (
	log "github.com/sirupsen/logrus"
	"layeh.com/radius"
)

type Context[TState any, TSettings any] interface {
	// GlobalState()

	ProtocolSettings() TSettings
	GetProtocolState(def func(Context[TState, TSettings]) TState) TState
	SetProtocolState(TState)

	EndInnerProtocol(func(p *radius.Packet) *radius.Packet)

	Log() *log.Entry
}
