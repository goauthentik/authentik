package connection

import (
	"bytes"
	"fmt"

	"github.com/gorilla/websocket"
	"github.com/wwt/guac"
)

var (
	internalOpcodeIns = fmt.Append(nil, len(guac.InternalDataOpcode), ".", guac.InternalDataOpcode)
	authentikOpcode   = []byte("0.authentik.")
)

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
				if bytes.HasPrefix(data, []byte(fileBulkPrefix)) {
					if err := c.sendBulkControl(data[len(fileBulkPrefix):]); err != nil {
						c.onError(err)
						return
					}
					continue
				}
				if bytes.HasPrefix(data, []byte(fileListPrefix)) {
					if err := c.sendFileList(data[len(fileListPrefix):]); err != nil {
						c.onError(err)
						return
					}
					continue
				}
				if bytes.HasPrefix(data, authentikOpcode) {
					switch string(bytes.Replace(data, authentikOpcode, []byte{}, 1)) {
					case "disconnect":
						_, e := w.Write([]byte(guac.NewInstruction("disconnect").String()))
						c.onError(e)
						return
					}
				}
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

func filterLegacyFileInstruction(ins []byte, blocked map[string]struct{}) (bool, error) {
	if !bytes.HasPrefix(ins, []byte("4.file,")) && !bytes.HasPrefix(ins, []byte("4.body,")) &&
		!bytes.HasPrefix(ins, []byte("4.blob,")) && !bytes.HasPrefix(ins, []byte("3.ack,")) &&
		!bytes.HasPrefix(ins, []byte("3.end,")) && !bytes.HasPrefix(ins, []byte("10.filesystem,")) {
		return false, nil
	}
	parsed, err := guac.Parse(ins)
	if err != nil {
		return false, err
	}
	stream := ""
	if len(parsed.Args) > 0 {
		stream = parsed.Args[0]
	}
	if parsed.Opcode == "filesystem" {
		return true, nil
	}
	if parsed.Opcode == "file" || parsed.Opcode == "body" {
		if stream != "" {
			blocked[stream] = struct{}{}
		}
		return true, nil
	}
	if _, found := blocked[stream]; found {
		if parsed.Opcode == "end" {
			delete(blocked, stream)
		}
		return true, nil
	}
	return false, nil
}

func (c *Connection) guacdToWs() {
	r := c.st.AcquireReader()
	buf := bytes.NewBuffer(make([]byte, 0, guac.MaxGuacMessage*2))
	blockedFileStreams := make(map[string]struct{})
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
			// guacd emits complete instructions. Drop legacy file streams before
			// they can enter the server's PostgreSQL-backed control channel.
			skip, parseErr := filterLegacyFileInstruction(ins, blockedFileStreams)
			if parseErr != nil {
				c.onError(parseErr)
				return
			}
			if skip {
				ins = nil
			}

			if _, e = buf.Write(ins); e != nil {
				c.log.WithError(e).Trace("Failed to buffer guacd to ws")
				c.onError(e)
				return
			}

			// if the buffer has more data in it or we've reached the max buffer size, send the data and reset
			if buf.Len() > 0 && (!r.Available() || buf.Len() >= guac.MaxGuacMessage) {
				if e = c.writeSocket(buf.Bytes()); e != nil {
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

// Guacamole data and metadata replies share one websocket writer.
func (c *Connection) writeSocket(data []byte) error {
	c.writeMu.Lock()
	defer c.writeMu.Unlock()
	return c.ws.WriteMessage(websocket.TextMessage, data)
}
