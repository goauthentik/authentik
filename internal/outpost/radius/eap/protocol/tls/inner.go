package tls

import (
	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

func (p *Payload) innerHandler(ctx protocol.Context) {
	// p.st.TLS.read
	// d, _ := io.ReadAll(p.st.TLS)
	err := p.Inner.Decode([]byte{})
	if err != nil {
		ctx.Log().WithError(err).Warning("TLS: failed to decode inner protocol")
		ctx.EndInnerProtocol(protocol.StatusError, nil)
		return
	}
	pl := p.Inner.Handle(ctx)
	enc, err := pl.Encode()
	p.st.TLS.Write(enc)
	// return &Payload{
	// 	Data: enc,
	// }
}
