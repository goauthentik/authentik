package web

import (
	"bufio"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"path"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestProxyDropsNonWebsocketUpgrade(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("TMPDIR", tmp)
	// Without gunicorn on PATH, Start only runs the health check.
	t.Setenv("PATH", t.TempDir())
	listener, err := net.Listen("unix", path.Join(tmp, CoreSocketName))
	if err != nil {
		t.Fatal(err)
	}
	received := make(chan http.Header, 1)
	upstream := &http.Server{Handler: http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/-/health/live/" {
			rw.WriteHeader(http.StatusOK)
			return
		}
		received <- r.Header.Clone()
		rw.WriteHeader(http.StatusNotFound)
	})}
	go func() { _ = upstream.Serve(listener) }()
	t.Cleanup(func() { _ = upstream.Close() })
	ws := NewWebServer()
	healthy := make(chan struct{})
	ws.g.AddHealthyCallback(func() { close(healthy) })
	go func() { _ = ws.g.Start() }()
	select {
	case <-healthy:
	case <-time.After(10 * time.Second):
		t.Fatal("upstream never became healthy")
	}
	front := httptest.NewServer(ws.mainRouter)
	t.Cleanup(front.Close)
	conn, err := net.Dial("tcp", front.Listener.Addr().String())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	_, err = io.WriteString(conn, "GET /api/v3/root/config/ HTTP/1.1\r\nHost: authentik.company\r\nConnection: upgrade\r\nUpgrade: websocket, h2c\r\n\r\n")
	if err != nil {
		t.Fatal(err)
	}
	res, err := http.ReadResponse(bufio.NewReader(conn), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = res.Body.Close() }()

	assert.Equal(t, http.StatusNotFound, res.StatusCode)
	select {
	case header := <-received:
		assert.Equal(t, "", header.Get("Upgrade"))
		assert.Equal(t, "", header.Get("Connection"))
	case <-time.After(5 * time.Second):
		t.Fatal("upstream received no request")
	}
}

func TestProxyUpgradesWebsocket(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("TMPDIR", tmp)
	t.Setenv("PATH", t.TempDir())
	listener, err := net.Listen("unix", path.Join(tmp, CoreSocketName))
	if err != nil {
		t.Fatal(err)
	}
	upstream := &http.Server{Handler: http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/-/health/live/" {
			rw.WriteHeader(http.StatusOK)
			return
		}
		if r.Header.Get("Upgrade") != "websocket" {
			rw.WriteHeader(http.StatusBadRequest)
			return
		}
		upgraded, buf, err := http.NewResponseController(rw).Hijack()
		if err != nil {
			t.Error(err)
			return
		}
		defer func() { _ = upgraded.Close() }()
		_, _ = buf.WriteString("HTTP/1.1 101 Switching Protocols\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n\r\n")
		_ = buf.Flush()
	})}
	go func() { _ = upstream.Serve(listener) }()
	t.Cleanup(func() { _ = upstream.Close() })
	ws := NewWebServer()
	healthy := make(chan struct{})
	ws.g.AddHealthyCallback(func() { close(healthy) })
	go func() { _ = ws.g.Start() }()
	select {
	case <-healthy:
	case <-time.After(10 * time.Second):
		t.Fatal("upstream never became healthy")
	}
	front := httptest.NewServer(ws.mainRouter)
	t.Cleanup(front.Close)
	conn, err := net.Dial("tcp", front.Listener.Addr().String())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = conn.Close() })

	_, err = io.WriteString(conn, "GET /ws/client/ HTTP/1.1\r\nHost: authentik.company\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n")
	if err != nil {
		t.Fatal(err)
	}
	res, err := http.ReadResponse(bufio.NewReader(conn), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = res.Body.Close() }()

	assert.Equal(t, http.StatusSwitchingProtocols, res.StatusCode)
}
