package peap

import (
	"encoding/binary"
)

type AVPType uint16

const (
	AVPAckResult AVPType = 3
)

type ExtensionAVP struct {
	Mandatory bool
	Type      AVPType // 14-bit field
	Length    uint16
	Value     []byte
}

func (eavp ExtensionAVP) Encode() []byte {
	buff := []byte{
		0,
		0,
		0,
		0,
	}
	t := uint16(eavp.Type)
	// Type is a 14-bit number, the highest bit is the mandatory flag
	if eavp.Mandatory {
		t = t | 0b1000000000000000
	}
	// The next bit is reserved and should always be set to 0
	t = t & 0b1011111111111111
	binary.BigEndian.PutUint16(buff[0:], t)
	binary.BigEndian.PutUint16(buff[2:], uint16(len(eavp.Value)))
	return append(buff, eavp.Value...)
}
