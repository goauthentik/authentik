package tls

import (
	"crypto/tls"
	"encoding/binary"
	"errors"
	"fmt"
	"slices"
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
	fmt.Printf("Got TLS packet % x\n", p.Flags)
	if !st.HasStarted {
		st.HasStarted = true
		return &Payload{
			Flags: FlagTLSStart,
		}, st
	}
	if st.HasMore() {
		return p.sendNextChunk(st)
	}

	fmt.Printf("decode tls raw '% x\n", p.Data)

	tc := NewTLSConnection(p.Data)
	if st.TLS == nil {
		fmt.Printf("no TLS connection in state yet, starting connection")
		st.TLS = tls.Server(tc, &tls.Config{
			GetConfigForClient: func(argHello *tls.ClientHelloInfo) (*tls.Config, error) {
				fmt.Printf("%+v\n", argHello)
				return nil, nil
			},
			ClientAuth:   tls.RequireAnyClientCert,
			Certificates: certs,
		})
		st.TLS.Handshake()
	}
	return p.sendDataChunked(tc.TLSData(), st)
}

const maxChunkSize = 1000

func (p *Payload) sendDataChunked(data []byte, st State) (*Payload, State) {
	flags := FlagLengthIncluded
	var dataToSend []byte
	if len(data) > maxChunkSize {
		fmt.Printf("Data needs to be chunked: %d\n", len(data))
		flags += FlagMoreFragments
		dataToSend = data[:maxChunkSize]
		remainingData := data[maxChunkSize:]
		// Chunk remaining data into correct chunks and add them to the list
		st.RemainingChunks = append(st.RemainingChunks, slices.Collect(slices.Chunk(remainingData, maxChunkSize))...)
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
	fmt.Printf("Sending next chunk\n")
	nextChunk := st.RemainingChunks[0]
	st.RemainingChunks = st.RemainingChunks[1:]
	flags := FlagLengthIncluded
	if st.HasMore() {
		fmt.Printf("More chunks left: %d\n", len(st.RemainingChunks))
		flags += FlagMoreFragments
	}
	fmt.Printf("Reporting size: %d\n", uint32((len(st.RemainingChunks)*maxChunkSize)+5))
	return &Payload{
		Flags:  flags,
		Length: uint32((len(st.RemainingChunks) * maxChunkSize) + 5),
		Data:   nextChunk,
	}, st
}
