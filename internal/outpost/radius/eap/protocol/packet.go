package protocol

type Payload interface {
	Decode(raw []byte) error
	Encode() ([]byte, error)
}

type Type uint8

const (
	TypeIdentity     Type = 1
	TypeMD5Challenge Type = 4
)
