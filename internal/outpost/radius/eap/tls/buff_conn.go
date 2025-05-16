package tls

import (
	"bytes"
	"context"
	"net"
	"time"

	log "github.com/sirupsen/logrus"
)

type BuffConn struct {
	reader *bytes.Buffer
	writer *bytes.Buffer

	ctx context.Context

	expectedWriterByteCount int
	writtenByteCount        int
}

func NewBuffConn(initialData []byte, ctx context.Context) *BuffConn {
	c := &BuffConn{
		reader: bytes.NewBuffer(initialData),
		writer: bytes.NewBuffer([]byte{}),
		ctx:    ctx,
	}
	return c
}

func (conn BuffConn) OutboundData() []byte {
	for {
		// TODO cancel with conn.ctx
		b := conn.writer.Bytes()
		if len(b) < 1 {
			log.Debug("TLS(buffcon): Attempted retrieve from empty buffer, stalling...")
			time.Sleep(1 * time.Second)
			continue
		}
		return b
	}
}

func (conn *BuffConn) UpdateData(data []byte) {
	conn.reader.Write(data)
	conn.writtenByteCount += len(data)
	log.Debugf("TLS(buffcon): Appending new data %d (total %d, expecting %d)", len(data), conn.writtenByteCount, conn.expectedWriterByteCount)
}

func (conn BuffConn) NeedsMoreData() bool {
	if conn.expectedWriterByteCount > 0 {
		return conn.reader.Len() < int(conn.expectedWriterByteCount)
	}
	return false
}

func (conn *BuffConn) Read(p []byte) (int, error) {
	for {
		// TODO cancel with conn.ctx
		n, err := conn.reader.Read(p)
		if n == 0 {
			log.Debugf("TLS(buffcon): Attempted read %d from empty buffer, stalling...", len(p))
			time.Sleep(100 * time.Millisecond)
			continue
		}
		if conn.expectedWriterByteCount > 0 && conn.writtenByteCount < int(conn.expectedWriterByteCount) {
			log.Debugf("TLS(buffcon): Attempted read %d while waiting for bytes %d, stalling...", len(p), conn.expectedWriterByteCount-conn.reader.Len())
			time.Sleep(100 * time.Millisecond)
			continue
		}
		if conn.expectedWriterByteCount > 0 && conn.writtenByteCount == int(conn.expectedWriterByteCount) {
			conn.expectedWriterByteCount = 0
		}
		if conn.reader.Len() == 0 {
			conn.writtenByteCount = 0
		}
		log.Debugf("TLS(buffcon): Read: %d from %d", len(p), n)
		return n, err
	}
}

func (conn BuffConn) Write(p []byte) (int, error) {
	log.Debugf("TLS(buffcon): Write: %d", len(p))
	return conn.writer.Write(p)
}

func (conn BuffConn) Close() error                       { return nil }
func (conn BuffConn) LocalAddr() net.Addr                { return nil }
func (conn BuffConn) RemoteAddr() net.Addr               { return nil }
func (conn BuffConn) SetDeadline(t time.Time) error      { return nil }
func (conn BuffConn) SetReadDeadline(t time.Time) error  { return nil }
func (conn BuffConn) SetWriteDeadline(t time.Time) error { return nil }
