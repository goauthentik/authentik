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

	expectedWriterByteCount int
	writtenByteCount        int
}

func NewTLSConnection(initialData []byte) *TLSConnection {
	c := &TLSConnection{
		reader: bytes.NewBuffer(initialData),
		writer: bytes.NewBuffer([]byte{}),
	}
	return c
}

func (conn TLSConnection) OutboundData() []byte {
	for {
		b := conn.writer.Bytes()
		if len(b) < 1 {
			log.Debug("TLS(buffer): Attempted retrieve from empty buffer, stalling...")
			time.Sleep(1 * time.Second)
			continue
		}
		return b
	}
}

func (conn *TLSConnection) UpdateData(data []byte) {
	conn.reader.Write(data)
	conn.writtenByteCount += len(data)
	log.Debugf("TLS(buffer): Appending new data %d (total %d, expecting %d)", len(data), conn.writtenByteCount, conn.expectedWriterByteCount)
}

func (conn TLSConnection) NeedsMoreData() bool {
	if conn.expectedWriterByteCount > 0 {
		return conn.reader.Len() < int(conn.expectedWriterByteCount)
	}
	return false
}

func (conn *TLSConnection) Read(p []byte) (int, error) {
	for {
		n, err := conn.reader.Read(p)
		if n == 0 {
			log.Debugf("TLS(buffer): Attempted read %d from empty buffer, stalling...", len(p))
			time.Sleep(500 * time.Millisecond)
			continue
		}
		if conn.expectedWriterByteCount > 0 && conn.writtenByteCount < int(conn.expectedWriterByteCount) {
			log.Debugf("TLS(buffer): Attempted read %d while waiting for bytes %d, stalling...", len(p), conn.expectedWriterByteCount-conn.reader.Len())
			time.Sleep(500 * time.Millisecond)
			continue
		}
		if conn.expectedWriterByteCount > 0 && conn.writtenByteCount == int(conn.expectedWriterByteCount) {
			conn.expectedWriterByteCount = 0
		}
		if conn.reader.Len() == 0 {
			conn.writtenByteCount = 0
		}
		log.Debugf("TLS(buffer): Read: %d from %d", len(p), n)
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
