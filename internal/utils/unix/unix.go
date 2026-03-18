package unix

import (
	"net"
	"time"
)

type Listener struct {
	ln *net.UnixListener
}

type Conn struct {
	c net.Conn
}

func Listen(path string) (*Listener, error) {
	addr, err := net.ResolveUnixAddr("unix", path)
	if err != nil {
		return nil, err
	}
	ln, err := net.ListenUnix("unix", addr)
	if err != nil {
		return nil, err
	}
	return &Listener{
		ln: ln,
	}, nil
}

func (l *Listener) Accept() (net.Conn, error) {
	c, err := l.ln.Accept()
	if err != nil {
		return nil, err
	}
	return &Conn{c: c}, nil
}

func (l *Listener) Close() error {
	return l.ln.Close()
}

func (l *Listener) Addr() net.Addr {
	return l.ln.Addr()
}

func (c *Conn) Read(b []byte) (int, error) {
	return c.c.Read(b)
}

func (c *Conn) Write(b []byte) (n int, err error) {
	return c.c.Write(b)
}

func (c *Conn) Close() error {
	return c.c.Close()
}

func (c *Conn) LocalAddr() net.Addr {
	return &net.TCPAddr{IP: net.IPv6loopback, Port: 0}
}

func (c *Conn) RemoteAddr() net.Addr {
	return &net.TCPAddr{IP: net.IPv6loopback, Port: 0}
}

func (c *Conn) SetDeadline(t time.Time) error {
	return c.c.SetDeadline(t)
}

func (c *Conn) SetReadDeadline(t time.Time) error {
	return c.c.SetReadDeadline(t)
}

func (c *Conn) SetWriteDeadline(t time.Time) error {
	return c.c.SetWriteDeadline(t)
}
