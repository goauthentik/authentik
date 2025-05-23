package peap

import "goauthentik.io/internal/outpost/radius/eap/protocol"

type State struct {
	SubState map[string]*protocol.State
}
