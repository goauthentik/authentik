package protocol

import "layeh.com/radius"

type Type uint8

type Code uint8

const (
	CodeRequest  Code = 1
	CodeResponse Code = 2
	CodeSuccess  Code = 3
	CodeFailure  Code = 4
)

type Payload interface {
	Decode(raw []byte) error
	Encode() ([]byte, error)
	Handle(ctx Context) Payload
	Type() Type
	Offerable() bool
	String() string
}

type Inner interface {
	HasInner() Payload
}

type ResponseModifier interface {
	ModifyRADIUSResponse(r *radius.Packet, q *radius.Packet) error
}
