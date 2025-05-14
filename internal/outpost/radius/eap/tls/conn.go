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
	// e.Request.Log().WithField("tls", len(c.reader.Bytes())).Debug("TLS Early")
	return c
}

//	func (conn *TLSConnection) SetCode(code radius.Code) {
//		conn.code = code
//	}
func (conn TLSConnection) Read(p []byte) (int, error) { return conn.reader.Read(p) }
func (conn TLSConnection) Write(p []byte) (int, error) {
	// final := make([]byte, 1)
	// final[0] = 128 // TLS Flags
	// final = append(final, p...)
	return conn.writer.Write(p)
	// return 0, nil
	// return conn.EAPConnection.Write(conn.code, final)
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

// func (conn TLSConnection) ContentType() layers.TLSType {
// 	return layers.TLSType(conn.TypeData[1])
// }
