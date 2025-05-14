package tls

import (
	"crypto/tls"
	"encoding/binary"
	"errors"
	"slices"

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
	log.WithField("flags", p.Flags).Debug("Got TLS Packet")
	if !st.HasStarted {
		st.HasStarted = true
		return &Payload{
			Flags: FlagTLSStart,
		}, st
	}
	if st.HasMore() {
		return p.sendNextChunk(st)
	}

	log.WithField("raw", debug.FormatBytes(p.Data)).Debug("TLS: Decode raw")

	tc := NewTLSConnection(p.Data)
	if st.TLS == nil {
		log.Debug("no TLS connection in state yet, starting connection")
		st.TLS = tls.Server(tc, &tls.Config{
			GetConfigForClient: func(argHello *tls.ClientHelloInfo) (*tls.Config, error) {
				log.Debugf("%+v\n", argHello)
				return nil, nil
			},
			ClientAuth:   tls.RequireAnyClientCert,
			Certificates: certs,
		})
		err := st.TLS.Handshake()
		log.WithError(err).Debug("TLS: Handshake error")
	}
	return p.sendDataChunked(tc.TLSData(), st)
}

const maxChunkSize = 1000

func (p *Payload) sendDataChunked(data []byte, st State) (*Payload, State) {
	flags := FlagLengthIncluded
	var dataToSend []byte
	if len(data) > maxChunkSize {
		log.WithField("length", len(data)).Debug("Data needs to be chunked")
		flags += FlagMoreFragments
		dataToSend = data[:maxChunkSize]
		remainingData := data[maxChunkSize:]
		// Chunk remaining data into correct chunks and add them to the list
		st.RemainingChunks = append(st.RemainingChunks, slices.Collect(slices.Chunk(remainingData, maxChunkSize))...)
		st.TotalPayloadSize = len(st.RemainingChunks) * maxChunkSize
	} else {
		dataToSend = data
	}
	return &Payload{
		Flags:  flags,
		Length: uint32(len(data) + 5),
		Data:   dataToSend,
	}, st
}

func (p *Payload) sendNextChunk(st State) (*Payload, State) {
	log.Debug("Sending next chunk")
	nextChunk := st.RemainingChunks[0]
	st.RemainingChunks = st.RemainingChunks[1:]
	flags := FlagLengthIncluded
	if st.HasMore() {
		log.WithField("chunks", len(st.RemainingChunks)).Debug("More chunks left")
		flags += FlagMoreFragments
	}
	log.WithField("length", st.TotalPayloadSize).Debug("Total payload size")
	return &Payload{
		Flags:  flags,
		Length: uint32(st.TotalPayloadSize),
		Data:   nextChunk,
	}, st
}
