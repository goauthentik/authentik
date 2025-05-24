package peap

import (
	"encoding/binary"
	"fmt"
)

type AVPType uint16

const (
	AVPAckResult AVPType = 3
)

const ExtensionHeaderSize = 4

type ExtensionAVP struct {
	Mandatory bool
	Type      AVPType // 14-bit field
	Length    uint16
	Value     []byte
}

func (eavp *ExtensionAVP) Decode(raw []byte) error {
	typ := binary.BigEndian.Uint16(raw[:2])
	// TODO fix this
	if typ&0b1000000000000000 == 0 {
		eavp.Mandatory = true
	}
	// TODO: Check reserved bit
	eavp.Type = AVPType(typ & 0b0011111111111111)
	eavp.Length = binary.BigEndian.Uint16(raw[2:4])
	val := raw[4:]
	if eavp.Length != uint16(len(val)) {
		return fmt.Errorf("PEAP-Extension: Invalid length: %d, should be %d", eavp.Length, len(val))
	}
	return nil
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
