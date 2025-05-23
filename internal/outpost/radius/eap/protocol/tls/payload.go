package tls

import (
	"context"
	"crypto/tls"
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"slices"
	"time"

	"github.com/avast/retry-go/v4"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
	"layeh.com/radius/vendors/microsoft"
)

const maxChunkSize = 1000
const staleConnectionTimeout = 10

const TypeTLS protocol.Type = 13

func Protocol() protocol.Payload {
	return &Payload{}
}

type Payload struct {
	Flags  Flag
	Length uint32
	Data   []byte

	st    *State
	Inner protocol.Payload
}

func (p *Payload) Type() protocol.Type {
	return TypeTLS
}

func (p *Payload) HasInner() protocol.Payload {
	return p.Inner
}

func (p *Payload) Offerable() bool {
	return true
}

func (p *Payload) Decode(raw []byte) error {
	p.Flags = Flag(raw[0])
	raw = raw[1:]
	if p.Flags&FlagLengthIncluded != 0 {
		if len(raw) < 4 {
			return errors.New("invalid size")
		}
		p.Length = binary.BigEndian.Uint32(raw)
		p.Data = raw[4:]
	} else {
		p.Data = raw[0:]
	}
	log.WithField("raw", debug.FormatBytes(p.Data)).WithField("size", len(p.Data)).WithField("flags", p.Flags).Trace("TLS: decode raw")
	return nil
}

func (p *Payload) Encode() ([]byte, error) {
	l := 1
	if p.Flags&FlagLengthIncluded != 0 {
		l += 4
	}
	buff := make([]byte, len(p.Data)+l)
	buff[0] = byte(p.Flags)
	if p.Flags&FlagLengthIncluded != 0 {
		buff[1] = byte(p.Length >> 24)
		buff[2] = byte(p.Length >> 16)
		buff[3] = byte(p.Length >> 8)
		buff[4] = byte(p.Length)
	}
	if len(p.Data) > 0 {
		copy(buff[5:], p.Data)
	}
	return buff, nil
}

func (p *Payload) Handle(ctx protocol.Context) protocol.Payload {
	defer func() {
		ctx.SetProtocolState(TypeTLS, p.st)
	}()
	if ctx.IsProtocolStart(TypeTLS) {
		p.st = NewState(ctx).(*State)
		return &Payload{
			Flags: FlagTLSStart,
		}
	}
	p.st = ctx.GetProtocolState(TypeTLS).(*State)

	if p.st.TLS == nil {
		p.tlsInit(ctx)
	} else if len(p.Data) > 0 {
		ctx.Log().Debug("TLS: Updating buffer with new TLS data from packet")
		if p.Flags&FlagLengthIncluded != 0 && p.st.Conn.expectedWriterByteCount == 0 {
			ctx.Log().Debugf("TLS: Expecting %d total bytes, will buffer", p.Length)
			p.st.Conn.expectedWriterByteCount = int(p.Length)
		} else if p.Flags&FlagLengthIncluded != 0 {
			ctx.Log().Debug("TLS: No length included, not buffering")
			p.st.Conn.expectedWriterByteCount = 0
		}
		p.st.Conn.UpdateData(p.Data)
		if !p.st.Conn.NeedsMoreData() && !p.st.HandshakeDone {
			// Wait for outbound data to be available
			p.st.Conn.OutboundData()
		}
	}
	// If we need more data, send the client the go-ahead
	if p.st.Conn.NeedsMoreData() {
		return &Payload{
			Flags:  FlagNone,
			Length: 0,
			Data:   []byte{},
		}
	}
	if p.st.HasMore() {
		return p.sendNextChunk()
	}
	if p.st.Conn.writer.Len() == 0 && p.st.HandshakeDone {
		if p.Inner != nil {
			ctx.Log().Debug("TLS: Handshake is done, delegating to inner protocol")
			p.innerHandler(ctx)
			return p.startChunkedTransfer(p.st.Conn.OutboundData())
		}
		defer p.st.ContextCancel()
		// If we don't have a final status from the handshake finished function, stall for time
		pst, _ := retry.DoWithData(
			func() (protocol.Status, error) {
				if p.st.FinalStatus == protocol.StatusUnknown {
					return p.st.FinalStatus, errStall
				}
				return p.st.FinalStatus, nil
			},
			retry.Context(p.st.Context),
			retry.Delay(10*time.Microsecond),
			retry.DelayType(retry.BackOffDelay),
			retry.MaxDelay(100*time.Millisecond),
			retry.Attempts(0),
		)
		ctx.EndInnerProtocol(pst, func(r *radius.Packet) *radius.Packet {
			microsoft.MSMPPERecvKey_Set(r, p.st.MPPEKey[:32])
			microsoft.MSMPPESendKey_Set(r, p.st.MPPEKey[64:64+32])
			return r
		})
		return nil
	}
	return p.startChunkedTransfer(p.st.Conn.OutboundData())
}

func (p *Payload) tlsInit(ctx protocol.Context) {
	ctx.Log().Debug("TLS: no TLS connection in state yet, starting connection")
	p.st.Context, p.st.ContextCancel = context.WithTimeout(context.Background(), staleConnectionTimeout*time.Second)
	p.st.Conn = NewBuffConn(p.Data, p.st.Context)
	cfg := ctx.ProtocolSettings().(TLSConfig).TLSConfig().Clone()

	if klp, ok := os.LookupEnv("SSLKEYLOGFILE"); ok {
		kl, err := os.OpenFile(klp, os.O_WRONLY|os.O_CREATE|os.O_APPEND, 0600)
		if err != nil {
			panic(err)
		}
		cfg.KeyLogWriter = kl
	}

	cfg.GetConfigForClient = func(chi *tls.ClientHelloInfo) (*tls.Config, error) {
		ctx.Log().Debugf("TLS: ClientHello: %+v\n", chi)
		p.st.ClientHello = chi
		return nil, nil
	}
	p.st.TLS = tls.Server(p.st.Conn, cfg)
	p.st.TLS.SetDeadline(time.Now().Add(staleConnectionTimeout * time.Second))
	go func() {
		err := p.st.TLS.HandshakeContext(p.st.Context)
		if err != nil {
			ctx.Log().WithError(err).Debug("TLS: Handshake error")
			p.st.FinalStatus = protocol.StatusError
			ctx.EndInnerProtocol(protocol.StatusError, func(p *radius.Packet) *radius.Packet {
				return p
			})
			return
		}
		ctx.Log().Debug("TLS: handshake done")
		p.tlsHandshakeFinished(ctx)
	}()
}

func (p *Payload) tlsHandshakeFinished(ctx protocol.Context) {
	cs := p.st.TLS.ConnectionState()
	label := "client EAP encryption"
	var context []byte
	switch cs.Version {
	case tls.VersionTLS10:
		ctx.Log().Debugf("TLS: Version %d (1.0)", cs.Version)
	case tls.VersionTLS11:
		ctx.Log().Debugf("TLS: Version %d (1.1)", cs.Version)
	case tls.VersionTLS12:
		ctx.Log().Debugf("TLS: Version %d (1.2)", cs.Version)
	case tls.VersionTLS13:
		ctx.Log().Debugf("TLS: Version %d (1.3)", cs.Version)
		label = "EXPORTER_EAP_TLS_Key_Material"
		context = []byte{byte(TypeTLS)}
	}
	ksm, err := cs.ExportKeyingMaterial(label, context, 64+64)
	ctx.Log().Debugf("TLS: ksm % x %v", ksm, err)
	p.st.MPPEKey = ksm
	p.st.HandshakeDone = true
	if p.Inner == nil {
		p.st.FinalStatus = ctx.ProtocolSettings().(Settings).HandshakeSuccessful(ctx, cs.PeerCertificates)
	}
}

func (p *Payload) startChunkedTransfer(data []byte) *Payload {
	if len(data) > maxChunkSize {
		log.WithField("length", len(data)).Debug("TLS: Data needs to be chunked")
		p.st.RemainingChunks = append(p.st.RemainingChunks, slices.Collect(slices.Chunk(data, maxChunkSize))...)
		p.st.TotalPayloadSize = len(data)
		return p.sendNextChunk()
	}
	log.WithField("length", len(data)).Debug("TLS: Sending data un-chunked")
	p.st.Conn.writer.Reset()
	return &Payload{
		Flags:  FlagLengthIncluded,
		Length: uint32(len(data)),
		Data:   data,
	}
}

func (p *Payload) sendNextChunk() *Payload {
	nextChunk := p.st.RemainingChunks[0]
	log.WithField("raw", debug.FormatBytes(nextChunk)).Debug("TLS: Sending next chunk")
	p.st.RemainingChunks = p.st.RemainingChunks[1:]
	flags := FlagLengthIncluded
	if p.st.HasMore() {
		log.WithField("chunks", len(p.st.RemainingChunks)).Debug("TLS: More chunks left")
		flags += FlagMoreFragments
	} else {
		// Last chunk, reset the connection buffers and pending payload size
		defer func() {
			log.Debug("TLS: Sent last chunk")
			p.st.Conn.writer.Reset()
			p.st.TotalPayloadSize = 0
		}()
	}
	log.WithField("length", p.st.TotalPayloadSize).Debug("TLS: Total payload size")
	return &Payload{
		Flags:  flags,
		Length: uint32(p.st.TotalPayloadSize),
		Data:   nextChunk,
	}
}

func (p *Payload) String() string {
	return fmt.Sprintf(
		"<TLS Packet HandshakeDone=%t, FinalStatus=%d, ClientHello=%v>",
		p.st.HandshakeDone,
		p.st.FinalStatus,
		p.st.ClientHello,
	)
}
