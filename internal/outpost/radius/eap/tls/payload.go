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
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/vendors/microsoft"
)

const maxChunkSize = 1000
const staleConnectionTimeout = 10

var certs = []tls.Certificate{}

func init() {
	// Testing
	cert, err := tls.LoadX509KeyPair(
		"../t/ca/out/cert_jens-mbp.lab.beryju.org.pem",
		"../t/ca/out/cert_jens-mbp.lab.beryju.org.key",
	)
	if err != nil {
		panic(err)
	}
	certs = append(certs, cert)
}

type Payload struct {
	Flags  Flag
	Length uint32
	Data   []byte
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

func (p *Payload) Handle(stt any) (protocol.Payload, *State) {
	if stt == nil {
		log.Debug("TLS: new state")
		stt = NewState()
	}
	st := stt.(*State)
	if !st.HasStarted {
		log.Debug("TLS: handshake starting")
		st.HasStarted = true
		return &Payload{
			Flags: FlagTLSStart,
		}, st
	}

	if st.TLS == nil {
		st = p.tlsInit(st)
	} else if len(p.Data) > 0 {
		log.Debug("TLS: Updating buffer with new TLS data from packet")
		if p.Flags&FlagLengthIncluded != 0 && st.Conn.expectedWriterByteCount == 0 {
			log.Debugf("TLS: Expecting %d total bytes, will buffer", p.Length)
			st.Conn.expectedWriterByteCount = int(p.Length)
		} else if p.Flags&FlagLengthIncluded != 0 {
			log.Debug("TLS: No length included, not buffering")
			st.Conn.expectedWriterByteCount = 0
		}
		st.Conn.UpdateData(p.Data)
		if !st.Conn.NeedsMoreData() {
			// Wait for outbound data to be available
			st.Conn.OutboundData()
		}
	}
	// If we need more data, send the client the go-ahead
	if st.Conn.NeedsMoreData() {
		return &Payload{
			Flags:  FlagNone,
			Length: 0,
			Data:   []byte{},
		}, st
	}
	if st.HasMore() {
		return p.sendNextChunk(st)
	}
	if st.Conn.writer.Len() == 0 && st.HandshakeDone {
		defer st.ContextCancel()
		return protocol.EmptyPayload{
			ModifyPacket: func(p *radius.Packet) *radius.Packet {
				p.Code = radius.CodeAccessAccept
				microsoft.MSMPPERecvKey_Set(p, st.MPPEKey[:32])
				microsoft.MSMPPESendKey_Set(p, st.MPPEKey[64:64+32])
				rfc2865.UserName_SetString(p, "foo")
				rfc2865.FramedMTU_Set(p, rfc2865.FramedMTU(1400))
				return p
			},
		}, st
	}
	return p.startChunkedTransfer(st.Conn.OutboundData(), st)
}

func (p *Payload) tlsInit(st *State) *State {
	log.Debug("TLS: no TLS connection in state yet, starting connection")
	st.Context, st.ContextCancel = context.WithTimeout(context.Background(), staleConnectionTimeout*time.Second)
	st.Conn = NewBuffConn(p.Data, st.Context)
	st.TLS = tls.Server(st.Conn, &tls.Config{
		GetConfigForClient: func(ch *tls.ClientHelloInfo) (*tls.Config, error) {
			log.Debugf("TLS: ClientHello: %+v\n", ch)
			st.ClientHello = ch
			return nil, nil
		},
		ClientAuth:   tls.RequireAnyClientCert,
		Certificates: certs,
	})
	go func() {
		err := st.TLS.HandshakeContext(st.Context)
		if err != nil {
			log.WithError(err).Debug("TLS: Handshake error")
			// TODO: Send a NAK to the client
			return
		}
		log.Debug("TLS: handshake done")
		p.tlsHandshakeFinished(st)
	}()
	return st
}

func (p *Payload) tlsHandshakeFinished(st *State) {
	cs := st.TLS.ConnectionState()
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
	st.MPPEKey = ksm
	st.HandshakeDone = true
}

func (p *Payload) startChunkedTransfer(data []byte, st *State) (*Payload, *State) {
	if len(data) > maxChunkSize {
		log.WithField("length", len(data)).Debug("TLS: Data needs to be chunked")
		st.RemainingChunks = append(st.RemainingChunks, slices.Collect(slices.Chunk(data, maxChunkSize))...)
		st.TotalPayloadSize = len(data)
		return p.sendNextChunk(st)
	}
	log.WithField("length", len(data)).Debug("TLS: Sending data un-chunked")
	st.Conn.writer.Reset()
	return &Payload{
		Flags:  FlagLengthIncluded,
		Length: uint32(len(data)),
		Data:   data,
	}, st
}

func (p *Payload) sendNextChunk(st *State) (*Payload, *State) {
	nextChunk := st.RemainingChunks[0]
	log.WithField("raw", debug.FormatBytes(nextChunk)).Debug("TLS: Sending next chunk")
	st.RemainingChunks = st.RemainingChunks[1:]
	flags := FlagLengthIncluded
	if st.HasMore() {
		log.WithField("chunks", len(st.RemainingChunks)).Debug("TLS: More chunks left")
		flags += FlagMoreFragments
	} else {
		// Last chunk, reset the connection buffers and pending payload size
		defer func() {
			log.Debug("TLS: Sent last chunk")
			st.Conn.writer.Reset()
			st.TotalPayloadSize = 0
		}()
	}
	log.WithField("length", st.TotalPayloadSize).Debug("TLS: Total payload size")
	return &Payload{
		Flags:  flags,
		Length: uint32(st.TotalPayloadSize),
		Data:   nextChunk,
	}, st
}
