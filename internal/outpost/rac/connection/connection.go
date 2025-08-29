package connection

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/websocket"
	log "github.com/sirupsen/logrus"
	"github.com/wwt/guac"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ak"
)

const guacAddr = "0.0.0.0:4822"

type Connection struct {
	log       *log.Entry
	st        *guac.SimpleTunnel
	ac        *ak.APIController
	ws        *websocket.Conn
	ctx       context.Context
	ctxCancel context.CancelFunc
	OnError   func(error)
	closing   bool
}

func NewConnection(ac *ak.APIController, forChannel string, cfg *guac.Config) (*Connection, error) {
	ctx, canc := context.WithCancel(context.Background())
	c := &Connection{
		ac:        ac,
		log:       log.WithField("connection", forChannel),
		ctx:       ctx,
		ctxCancel: canc,
		OnError:   func(err error) {},
		closing:   false,
	}
	err := c.initGuac(cfg)
	if err != nil {
		return nil, err
	}
	err = c.initSocket(forChannel)
	if err != nil {
		_ = c.st.Close()
		return nil, err
	}
	c.initMirror()
	return c, nil
}

func (c *Connection) initSocket(forChannel string) error {
	pathTemplate := "%s://%s/ws/outpost_rac/%s/"
	scheme := strings.ReplaceAll(c.ac.Client.GetConfig().Scheme, "http", "ws")

	authHeader := fmt.Sprintf("Bearer %s", c.ac.Token())

	header := http.Header{
		"Authorization": []string{authHeader},
		"User-Agent":    []string{constants.UserAgentOutpost()},
	}

	dialer := websocket.Dialer{
		Proxy:            http.ProxyFromEnvironment,
		HandshakeTimeout: 10 * time.Second,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: config.Get().AuthentikInsecure,
		},
	}

	url := fmt.Sprintf(pathTemplate, scheme, c.ac.Client.GetConfig().Host, forChannel)
	ws, _, err := dialer.Dial(url, header)
	if err != nil {
		c.log.WithError(err).Warning("failed to connect websocket")
		return err
	}
	c.ws = ws
	return nil
}

func (c *Connection) initGuac(cfg *guac.Config) error {
	addr, err := net.ResolveTCPAddr("tcp", guacAddr)
	if err != nil {
		return err
	}

	conn, err := net.DialTCP("tcp", nil, addr)
	if err != nil {
		return err
	}

	stream := guac.NewStream(conn, guac.SocketTimeout)

	err = stream.Handshake(cfg)
	if err != nil {
		return err
	}
	st := guac.NewSimpleTunnel(stream)
	c.st = st
	return nil
}

func (c *Connection) initMirror() {
	go c.wsToGuacd()
	go c.guacdToWs()
}

func (c *Connection) onError(err error) {
	if c.closing {
		return
	}
	c.closing = true
	e := c.st.Close()
	if e != nil {
		c.log.WithError(e).Warning("failed to close guacd connection")
	}
	c.log.WithError(err).Info("removing connection")
	c.ctxCancel()
	c.OnError(err)
}
