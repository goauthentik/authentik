package unix

import (
	"net"
)

type Listener struct {
	*net.UnixListener
}

type Conn struct {
	net.Conn
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
		ln,
	}, nil
}

func (l *Listener) Accept() (net.Conn, error) {
	c, err := l.UnixListener.Accept()
	if err != nil {
		return nil, err
	}
	return &Conn{c}, nil
}

func (c *Conn) LocalAddr() net.Addr {
	return &net.TCPAddr{IP: net.IPv6loopback, Port: 0}
}

func (c *Conn) RemoteAddr() net.Addr {
	return &net.TCPAddr{IP: net.IPv6loopback, Port: 0}
}
