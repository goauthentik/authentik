package protocol

type Payload interface {
	Decode(raw []byte) error
	Encode() ([]byte, error)
	Handle(ctx Context) Payload
	Type() Type
	Offerable() bool
}

type Type uint8
