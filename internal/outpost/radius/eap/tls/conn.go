package tls

import (
	"bytes"
	"net"
	"time"
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

func (conn TLSConnection) Read(p []byte) (int, error) { return conn.reader.Read(p) }
func (conn TLSConnection) Write(p []byte) (int, error) {
	return conn.writer.Write(p)
}
func (conn TLSConnection) Close() error                       { return nil }
func (conn TLSConnection) LocalAddr() net.Addr                { return nil }
func (conn TLSConnection) RemoteAddr() net.Addr               { return nil }
func (conn TLSConnection) SetDeadline(t time.Time) error      { return nil }
func (conn TLSConnection) SetReadDeadline(t time.Time) error  { return nil }
func (conn TLSConnection) SetWriteDeadline(t time.Time) error { return nil }

func (conn TLSConnection) TLSData() []byte {
	return conn.writer.Bytes()
}
