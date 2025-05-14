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
)

type Payload struct {
	Flags  Flag
	Length uint32
	Data   []byte
}

func (p *Payload) Decode(raw []byte) error {
	p.Flags = Flag(raw[0])
	if p.Flags&FlagLengthIncluded != 0 {
		if len(raw) < 4 {
			return errors.New("invalid size")
		}
		p.Length = binary.BigEndian.Uint32(raw)
		p.Data = raw[5:]
	} else {
		p.Data = raw[1:]
	}
	log.WithField("raw", debug.FormatBytes(p.Data)).WithField("flags", p.Flags).Debug("TLS: decode raw")
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

func (p *Payload) Handle(stt any) (*Payload, State) {
	if stt == nil {
		stt = NewState()
	}
	st := stt.(State)
	if !st.HasStarted {
		st.HasStarted = true
		return &Payload{
			Flags: FlagTLSStart,
		}, st
	}

	if st.TLS == nil {
		log.Debug("TLS: no TLS connection in state yet, starting connection")
		st.Conn = NewTLSConnection(p.Data)
		st.TLS = tls.Server(st.Conn, &tls.Config{
			GetConfigForClient: func(argHello *tls.ClientHelloInfo) (*tls.Config, error) {
				log.Debugf("TLS: ClientHello: %+v\n", argHello)
				return nil, nil
			},
			ClientAuth:   tls.RequireAnyClientCert,
			Certificates: certs,
		})
		st.Context, _ = context.WithTimeout(context.Background(), 30*time.Second)
		go func() {
			err := st.TLS.HandshakeContext(st.Context)
			if err != nil {
				log.WithError(err).Debug("TLS: Handshake error")
			}
		}()
	} else if len(p.Data) > 0 {
		log.Debug("TLS: Updating buffer with new TLS data from packet")
		st.Conn.UpdateData(p.Data)
	}
	if st.HasMore() {
		return p.sendNextChunk(st)
	}
	return p.startChunkedTransfer(st.Conn.TLSData(), st)
}

const maxChunkSize = 1000

func (p *Payload) startChunkedTransfer(data []byte, st State) (*Payload, State) {
	flags := FlagLengthIncluded
	var dataToSend []byte
	if len(data) > maxChunkSize {
		log.WithField("length", len(data)).Debug("TLS: Data needs to be chunked")
		flags += FlagMoreFragments
		dataToSend = data[:maxChunkSize]
		remainingData := data[maxChunkSize:]
		// Chunk remaining data into correct chunks and add them to the list
		st.RemainingChunks = append(st.RemainingChunks, slices.Collect(slices.Chunk(remainingData, maxChunkSize))...)
		st.TotalPayloadSize = len(data)
	} else {
		dataToSend = data
	}
	return &Payload{
		Flags:  flags,
		Length: uint32(st.TotalPayloadSize),
		Data:   dataToSend,
	}, st
}

func (p *Payload) sendNextChunk(st State) (*Payload, State) {
	log.Debug("TLS: Sending next chunk")
	nextChunk := st.RemainingChunks[0]
	st.RemainingChunks = st.RemainingChunks[1:]
	flags := FlagLengthIncluded
	if st.HasMore() {
		log.WithField("chunks", len(st.RemainingChunks)).Debug("TLS: More chunks left")
		flags += FlagMoreFragments
	}
	log.WithField("length", st.TotalPayloadSize).Debug("TLS: Total payload size")
	return &Payload{
		Flags:  flags,
		Length: uint32(st.TotalPayloadSize),
		Data:   nextChunk,
	}, st
}
