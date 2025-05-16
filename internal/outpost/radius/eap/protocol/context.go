package protocol

import (
	log "github.com/sirupsen/logrus"
	"layeh.com/radius"
)

type Status int

const (
	StatusUnknown Status = iota
	StatusSuccess
	StatusError
)

type Context interface {
	Packet() *radius.Request

	ProtocolSettings() interface{}
	GetProtocolState(def func(Context) interface{}) interface{}
	SetProtocolState(interface{})

	EndInnerProtocol(Status, func(p *radius.Packet) *radius.Packet)

	Log() *log.Entry
}
