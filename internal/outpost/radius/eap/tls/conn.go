package tls

import (
	"bytes"
	"net"
	"time"

	log "github.com/sirupsen/logrus"
)

type TLSConnection struct {
	reader *bytes.Buffer
	writer *bytes.Buffer
}

func NewTLSConnection(initialData []byte) TLSConnection {
	c := TLSConnection{
		reader: bytes.NewBuffer(initialData),
		writer: bytes.NewBuffer([]byte{}),
	}
	return c
}

func (conn TLSConnection) TLSData() []byte {
	return conn.writer.Bytes()
}

func (conn TLSConnection) UpdateData(data []byte) {
	conn.reader.Reset()
	conn.reader.Write(data)
}

// ----

func (conn TLSConnection) Read(p []byte) (int, error) {
	log.Debugf("TLS(buffer): Read: %d from %d", len(p), conn.reader.Len())
	for {
		n, err := conn.reader.Read(p)
		if n == 0 {
			log.Debug("TLS(buffer): Attempted read from empty buffer, stalling...")
			time.Sleep(1 * time.Second)
			continue
		}
		return n, err
	}
}

func (conn TLSConnection) Write(p []byte) (int, error) {
	log.Debugf("TLS(buffer): Write: %d", len(p))
	return conn.writer.Write(p)
}

func (conn TLSConnection) Close() error                       { return nil }
func (conn TLSConnection) LocalAddr() net.Addr                { return nil }
func (conn TLSConnection) RemoteAddr() net.Addr               { return nil }
func (conn TLSConnection) SetDeadline(t time.Time) error      { return nil }
func (conn TLSConnection) SetReadDeadline(t time.Time) error  { return nil }
func (conn TLSConnection) SetWriteDeadline(t time.Time) error { return nil }
