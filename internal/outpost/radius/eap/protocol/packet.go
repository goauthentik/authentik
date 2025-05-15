package protocol

type Payload interface {
	Decode(raw []byte) error
	Encode() ([]byte, error)
}
