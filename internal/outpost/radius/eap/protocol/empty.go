package protocol

import "layeh.com/radius"

type EmptyPayload struct {
	ModifyPacket func(p *radius.Packet) *radius.Packet
}

func (ep EmptyPayload) Decode(raw []byte) error {
	return nil
}
func (ep EmptyPayload) Encode() ([]byte, error) {
	return []byte{}, nil
}
