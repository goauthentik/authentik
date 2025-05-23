package mschapv2

import "encoding/binary"

type SuccessRequest struct {
	*Payload
	Authenticator []byte
}

// A success request is encoded slightly differently, it doesn't have a challenge and as such
// doesn't need to encode the length of it
func (sr *SuccessRequest) Encode() ([]byte, error) {
	encoded := []byte{
		byte(sr.OpCode),
		sr.MSCHAPv2ID,
		0,
		0,
	}
	encoded = append(encoded, sr.Authenticator...)
	sr.MSLength = uint16(len(encoded))
	binary.BigEndian.PutUint16(encoded[2:], sr.MSLength)
	return encoded, nil
}
