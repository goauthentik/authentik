package protocol

import (
	log "github.com/sirupsen/logrus"
	"layeh.com/radius"
)

type Context interface {
	// GlobalState()

	ProtocolSettings() interface{}
	GetProtocolState(def func(Context) interface{}) interface{}
	SetProtocolState(interface{})

	EndInnerProtocol(func(p *radius.Packet) *radius.Packet)

	Log() *log.Entry
}
