package protocol

type EmptyPayload struct {
}

func (ep EmptyPayload) Decode(raw []byte) error {
	return nil
}
func (ep EmptyPayload) Encode() ([]byte, error) {
	return []byte{}, nil
}
