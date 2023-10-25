package connection

import (
	"bytes"
	"fmt"

	"github.com/gorilla/websocket"
	"github.com/wwt/guac"
)

var internalOpcodeIns = []byte(fmt.Sprint(len(guac.InternalDataOpcode), ".", guac.InternalDataOpcode))

// MessageReader wraps a websocket connection and only permits Reading
type MessageReader interface {
	// ReadMessage should return a single complete message to send to guac
	ReadMessage() (int, []byte, error)
}

func (c *Connection) wsToGuacd() {
	w := c.st.AcquireWriter()
	for {
		select {
		default:
			_, data, e := c.ws.ReadMessage()
			if e != nil {
				c.log.WithError(e).Trace("Error reading message from ws")
				c.onError(e)
				return
			}

			if bytes.HasPrefix(data, internalOpcodeIns) {
				// messages starting with the InternalDataOpcode are never sent to guacd
				continue
			}

			if _, e = w.Write(data); e != nil {
				c.log.WithError(e).Trace("Failed writing to guacd")
				c.onError(e)
				return
			}
		case <-c.ctx.Done():
			return
		}
	}
}

// MessageWriter wraps a websocket connection and only permits Writing
type MessageWriter interface {
	// WriteMessage writes one or more complete guac commands to the websocket
	WriteMessage(int, []byte) error
}

func (c *Connection) guacdToWs() {
	r := c.st.AcquireReader()
	buf := bytes.NewBuffer(make([]byte, 0, guac.MaxGuacMessage*2))
	for {
		select {
		default:
			ins, e := r.ReadSome()
			if e != nil {
				c.log.WithError(e).Trace("Error reading from guacd")
				c.onError(e)
				return
			}

			if bytes.HasPrefix(ins, internalOpcodeIns) {
				// messages starting with the InternalDataOpcode are never sent to the websocket
				continue
			}

			if _, e = buf.Write(ins); e != nil {
				c.log.WithError(e).Trace("Failed to buffer guacd to ws")
				c.onError(e)
				return
			}

			// if the buffer has more data in it or we've reached the max buffer size, send the data and reset
			if !r.Available() || buf.Len() >= guac.MaxGuacMessage {
				if e = c.ws.WriteMessage(1, buf.Bytes()); e != nil {
					if e == websocket.ErrCloseSent {
						return
					}
					c.log.WithError(e).Trace("Failed sending message to ws")
					c.onError(e)
					return
				}
				buf.Reset()
			}
		case <-c.ctx.Done():
			return
		}
	}
}
