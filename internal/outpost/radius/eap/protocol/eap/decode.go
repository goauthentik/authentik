package eap

import (
	"fmt"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

func EmptyPayload(settings protocol.Settings, t protocol.Type) (protocol.Payload, protocol.Type, error) {
	for _, cons := range settings.Protocols {
		np := cons()
		if np.Type() == t {
			return np, np.Type(), nil
		}
		// If the protocol has an inner protocol, return the original type but the code for the inner protocol
		if i, ok := np.(protocol.Inner); ok {
			if ii := i.HasInner(); ii != nil {
				return np, ii.Type(), nil
			}
		}
	}
	return nil, protocol.Type(0), fmt.Errorf("unsupported EAP type %d", t)
}
