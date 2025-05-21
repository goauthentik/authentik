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
	StatusNextProtocol
)

type Context interface {
	Packet() *radius.Request

	ProtocolSettings() interface{}

	ForInnerProtocol(p Type) Context

	StateForProtocol(p Type) interface{}
	GetProtocolState() interface{}
	SetProtocolState(interface{})

	IsProtocolStart() bool
	EndInnerProtocol(Status, func(p *radius.Packet) *radius.Packet)

	Log() *log.Entry
}
