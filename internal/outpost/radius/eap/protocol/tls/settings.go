package tls

import (
	"crypto/tls"
	"crypto/x509"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

type Settings struct {
	Config              *tls.Config
	HandshakeSuccessful func(ctx protocol.Context, certs []*x509.Certificate) protocol.Status
}
