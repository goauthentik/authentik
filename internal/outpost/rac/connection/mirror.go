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
		_, data, err := c.ws.ReadMessage()
		if err != nil {
			c.log.WithError(err).Trace("Error reading message from ws")
			return
		}

		if bytes.HasPrefix(data, internalOpcodeIns) {
			// messages starting with the InternalDataOpcode are never sent to guacd
			continue
		}

		if _, err = w.Write(data); err != nil {
			c.log.WithError(err).Trace("Failed writing to guacd")
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
		ins, err := r.ReadSome()
		if err != nil {
			c.log.WithError(err).Trace("Error reading from guacd")
			return
		}

		if bytes.HasPrefix(ins, internalOpcodeIns) {
			// messages starting with the InternalDataOpcode are never sent to the websocket
			continue
		}

		if _, err = buf.Write(ins); err != nil {
			c.log.WithError(err).Trace("Failed to buffer guacd to ws")
			return
		}

		// if the buffer has more data in it or we've reached the max buffer size, send the data and reset
		if !r.Available() || buf.Len() >= guac.MaxGuacMessage {
			if err = c.ws.WriteMessage(1, buf.Bytes()); err != nil {
				if err == websocket.ErrCloseSent {
					return
				}
				c.log.WithError(err).Trace("Failed sending message to ws")
				return
			}
			buf.Reset()
		}
	}
}
