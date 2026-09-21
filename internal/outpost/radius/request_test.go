package radius

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"layeh.com/radius"
)

var (
	radiusPacketAccReq = []byte{0x1, 0x8f, 0x0, 0x4d, 0x4a, 0xd5, 0x47, 0x98, 0xbf, 0x18, 0xe, 0x4b, 0x6a, 0xdd, 0x0, 0xc7, 0x99, 0xb4, 0xa6, 0x57, 0x50, 0x12, 0xa5, 0xf7, 0x16, 0x88, 0xc5, 0xd8, 0xd9, 0xec, 0x19, 0xc8, 0x51, 0x47, 0x9, 0x5f, 0xe5, 0x60, 0x1, 0x9, 0x61, 0x6b, 0x61, 0x64, 0x6d, 0x69, 0x6e, 0x2, 0x12, 0x37, 0x36, 0x8, 0xa3, 0x72, 0x20, 0xf, 0xf4, 0xc0, 0xc, 0xd2, 0x40, 0xc1, 0xc3, 0x3f, 0xef, 0x4, 0x6, 0xa, 0x78, 0x14, 0x4c, 0x5, 0x6, 0x0, 0x0, 0x0, 0xa}
)

func Test_Request_validateMessageAuthenticator_valid(t *testing.T) {
	p, err := radius.Parse(radiusPacketAccReq, []byte("foo"))
	assert.NoError(t, err)
	req := RadiusRequest{
		Request: &radius.Request{
			Packet: p,
		},
		pi: &ProviderInstance{
			SharedSecret: []byte("foo"),
		},
	}
	assert.NoError(t, req.validateMessageAuthenticator())
}

func Test_Request_validateMessageAuthenticator_invalid(t *testing.T) {
	p, err := radius.Parse(radiusPacketAccReq, []byte("bar"))
	assert.NoError(t, err)
	req := RadiusRequest{
		Request: &radius.Request{
			Packet: p,
		},
		pi: &ProviderInstance{
			SharedSecret: []byte("bar"),
		},
	}
	assert.Error(t, req.validateMessageAuthenticator(), ErrInvalidMessageAuthenticator)
}

func Test_Request_setMessageAuthenticator(t *testing.T) {
	p, err := radius.Parse(radiusPacketAccReq, []byte("foo"))
	assert.NoError(t, err)
	req := RadiusRequest{
		Request: &radius.Request{
			Packet: p,
		},
		pi: &ProviderInstance{
			SharedSecret: []byte("foo"),
		},
	}
	res := p.Response(radius.CodeAccessAccept)
	assert.NoError(t, req.setMessageAuthenticator(res))

	nr := RadiusRequest{
		Request: &radius.Request{
			Packet: res,
		},
		pi: req.pi,
	}
	assert.NoError(t, nr.validateMessageAuthenticator())
}
