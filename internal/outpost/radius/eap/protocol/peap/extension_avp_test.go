package peap_test

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/radius/eap/protocol/peap"
)

func TestEncode(t *testing.T) {
	eavp := peap.ExtensionAVP{
		Mandatory: true,
		Type:      peap.AVPType(3),
	}
	assert.Equal(t, []byte{0x80, 0x3, 0x0, 0x0}, eavp.Encode())
}

func TestDecode(t *testing.T) {
	eavp := peap.ExtensionAVP{}
	err := eavp.Decode([]byte{0x80, 0x3, 0x0, 0x0})
	assert.NoError(t, err)
	assert.True(t, eavp.Mandatory)
	assert.Equal(t, peap.AVPType(3), eavp.Type)
}

func TestDecode_Invalid_ReservedBitSet(t *testing.T) {
	eavp := peap.ExtensionAVP{}
	err := eavp.Decode([]byte{0xc0, 0x3, 0x0, 0x0})
	assert.ErrorIs(t, err, peap.ErrorReservedBitSet)
}

func TestDecode_Invalid_Length(t *testing.T) {
	eavp := peap.ExtensionAVP{}
	err := eavp.Decode([]byte{0x80, 0x3, 0x0, 0x0, 0x0})
	assert.NotNil(t, err)
}
