package web

import (
	"net"
	"time"

	log "github.com/sirupsen/logrus"
)

// tcpKeepAliveListener sets TCP keep-alive timeouts on accepted
// connections. It's used by ListenAndServe and ListenAndServeTLS so
// dead TCP connections (e.g. closing laptop mid-download) eventually
// go away.
type TCPKeepAliveListener struct {
	*net.TCPListener
}

func (ln TCPKeepAliveListener) Accept() (net.Conn, error) {
	tc, err := ln.AcceptTCP()
	if err != nil {
		return nil, err
	}
	err = tc.SetKeepAlive(true)
	if err != nil {
		log.WithError(err).Warning("Error setting Keep-Alive")
	}
	err = tc.SetKeepAlivePeriod(3 * time.Minute)
	if err != nil {
		log.WithError(err).Warning("Error setting Keep-Alive period")
	}
	return tc, nil
}
