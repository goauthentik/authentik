package tls

import (
	"context"
	"crypto/tls"
	"encoding/binary"
	"errors"
	"slices"
	"time"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/radius/eap/debug"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"layeh.com/radius"
	"layeh.com/radius/vendors/microsoft"
)

const maxChunkSize = 1000
const staleConnectionTimeout = 10

type Payload struct {
	Flags  Flag
	Length uint32
	Data   []byte

	st *State
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
	log.WithField("raw", debug.FormatBytes(p.Data)).WithField("size", len(p.Data)).WithField("flags", p.Flags).Debug("TLS: decode raw")
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
	p.st = ctx.GetProtocolState(NewState).(*State)
	defer ctx.SetProtocolState(p.st)
	if !p.st.HasStarted {
		log.Debug("TLS: handshake starting")
		p.st.HasStarted = true
		return &Payload{
			Flags: FlagTLSStart,
		}
	}

	if p.st.TLS == nil {
		p.tlsInit(ctx)
	} else if len(p.Data) > 0 {
		log.Debug("TLS: Updating buffer with new TLS data from packet")
		if p.Flags&FlagLengthIncluded != 0 && p.st.Conn.expectedWriterByteCount == 0 {
			log.Debugf("TLS: Expecting %d total bytes, will buffer", p.Length)
			p.st.Conn.expectedWriterByteCount = int(p.Length)
		} else if p.Flags&FlagLengthIncluded != 0 {
			log.Debug("TLS: No length included, not buffering")
			p.st.Conn.expectedWriterByteCount = 0
		}
		p.st.Conn.UpdateData(p.Data)
		if !p.st.Conn.NeedsMoreData() {
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
		defer p.st.ContextCancel()
		ctx.EndInnerProtocol(func(r *radius.Packet) *radius.Packet {
			r.Code = radius.CodeAccessAccept
			microsoft.MSMPPERecvKey_Set(r, p.st.MPPEKey[:32])
			microsoft.MSMPPESendKey_Set(r, p.st.MPPEKey[64:64+32])
			return r
		})
		return nil
	}
	return p.startChunkedTransfer(p.st.Conn.OutboundData())
}

func (p *Payload) tlsInit(ctx protocol.Context) {
	log.Debug("TLS: no TLS connection in state yet, starting connection")
	p.st.Context, p.st.ContextCancel = context.WithTimeout(context.Background(), staleConnectionTimeout*time.Second)
	p.st.Conn = NewBuffConn(p.Data, p.st.Context)
	cfg := ctx.ProtocolSettings().(Settings).Config.Clone()
	cfg.GetConfigForClient = func(chi *tls.ClientHelloInfo) (*tls.Config, error) {
		log.Debugf("TLS: ClientHello: %+v\n", chi)
		p.st.ClientHello = chi
		return nil, nil
	}
	p.st.TLS = tls.Server(p.st.Conn, cfg)
	go func() {
		err := p.st.TLS.HandshakeContext(p.st.Context)
		if err != nil {
			log.WithError(err).Debug("TLS: Handshake error")
			// TODO: Send a NAK to the client
			return
		}
		log.Debug("TLS: handshake done")
		p.tlsHandshakeFinished()
	}()
}

func (p *Payload) tlsHandshakeFinished() {
	cs := p.st.TLS.ConnectionState()
	label := "client EAP encryption"
	var context []byte
	switch cs.Version {
	case tls.VersionTLS10:
		log.Debugf("TLS: Version %d (1.0)", cs.Version)
	case tls.VersionTLS11:
		log.Debugf("TLS: Version %d (1.1)", cs.Version)
	case tls.VersionTLS12:
		log.Debugf("TLS: Version %d (1.2)", cs.Version)
	case tls.VersionTLS13:
		log.Debugf("TLS: Version %d (1.3)", cs.Version)
		label = "EXPORTER_EAP_TLS_Key_Material"
		context = []byte{13}
	}
	ksm, err := cs.ExportKeyingMaterial(label, context, 64+64)
	log.Debugf("TLS: ksm % x %v", ksm, err)
	p.st.MPPEKey = ksm
	p.st.HandshakeDone = true
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
