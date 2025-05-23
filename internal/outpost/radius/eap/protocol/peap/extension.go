package peap

import (
	"errors"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

const TypePEAPExtension protocol.Type = 33

type ExtensionPayload struct {
	AVPs []ExtensionAVP
}

func (ep *ExtensionPayload) Decode(raw []byte) error {
	return errors.New("PEAP: Extension Payload does not support decoding")
}

func (ep *ExtensionPayload) Encode() ([]byte, error) {
	return []byte{}, nil
}

func (ep *ExtensionPayload) Handle(protocol.Context) protocol.Payload {
	return nil
}

func (ep *ExtensionPayload) Offerable() bool {
	return false
}

func (ep *ExtensionPayload) String() string {
	return "<PEAP Extension Payload>"
}

func (ep *ExtensionPayload) Type() protocol.Type {
	return TypePEAPExtension
}
