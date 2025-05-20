package tls

import (
	"bytes"
	"context"
	"errors"
	"net"
	"time"

	"github.com/avast/retry-go/v4"
	log "github.com/sirupsen/logrus"
)

type BuffConn struct {
	reader *bytes.Buffer
	writer *bytes.Buffer

	ctx context.Context

	expectedWriterByteCount int
	writtenByteCount        int

	retryOptions []retry.Option
}

func NewBuffConn(initialData []byte, ctx context.Context) *BuffConn {
	c := &BuffConn{
		reader: bytes.NewBuffer(initialData),
		writer: bytes.NewBuffer([]byte{}),
		ctx:    ctx,
		retryOptions: []retry.Option{
			retry.Context(ctx),
			retry.Delay(10 * time.Microsecond),
			retry.DelayType(retry.BackOffDelay),
			retry.MaxDelay(100 * time.Millisecond),
			retry.Attempts(0),
		},
	}
	return c
}

var errStall = errors.New("Stall")

func (conn BuffConn) OutboundData() []byte {
	d, _ := retry.DoWithData(
		func() ([]byte, error) {
			b := conn.writer.Bytes()
			if len(b) < 1 {
				return nil, errStall
			}
			return b, nil
		},
		conn.retryOptions...,
	)
	return d
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
	d, err := retry.DoWithData(
		func() (int, error) {
			if conn.reader.Len() == 0 {
				log.Debugf("TLS(buffcon): Attempted read %d from empty buffer, stalling...", len(p))
				return 0, errStall
			}
			if conn.expectedWriterByteCount > 0 {
				// If we're waiting for more data, we need to stall
				if conn.writtenByteCount < int(conn.expectedWriterByteCount) {
					log.Debugf("TLS(buffcon): Attempted read %d while waiting for bytes %d, stalling...", len(p), conn.expectedWriterByteCount-conn.reader.Len())
					return 0, errStall
				}
				// If we have all the data, reset how much we're expecting to still get
				if conn.writtenByteCount == int(conn.expectedWriterByteCount) {
					conn.expectedWriterByteCount = 0
				}
			}
			if conn.reader.Len() == 0 {
				conn.writtenByteCount = 0
			}
			n, err := conn.reader.Read(p)
			log.Debugf("TLS(buffcon): Read: %d into %d (total %d)", n, len(p), conn.reader.Len())
			return n, err
		},
		conn.retryOptions...,
	)
	return d, err
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
