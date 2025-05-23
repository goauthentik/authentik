package peap

import (
	"crypto/tls"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

type Settings struct {
	Config         *tls.Config
	InnerProtocols protocol.Settings
}

func (s Settings) TLSConfig() *tls.Config {
	return s.Config
}
