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
	if err != nil {
		ctx.Log().WithError(err).Warning("failed to encode inner protocol")
	}
	// p.st.Conn.expectedWriterByteCount = len(enc)
	_, err = p.st.TLS.Write(enc)
	if err != nil {
		ctx.Log().WithError(err).Warning("failed to write to TLS")
	}
	// return &Payload{
	// 	Data: enc,
	// }
}
