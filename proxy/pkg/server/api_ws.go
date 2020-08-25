package server

import (
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/go-openapi/strfmt"
	"github.com/gorilla/websocket"
	"github.com/recws-org/recws"
)

func (ac *APIController) initWS(pbURL url.URL, outpostUUID strfmt.UUID) {
	pathTemplate := "%s://%s/ws/outpost/%s/"
	scheme := strings.ReplaceAll(pbURL.Scheme, "http", "ws")

	header := http.Header{
		"Authorization": []string{ac.token},
	}

	ws := recws.RecConn{
		// KeepAliveTimeout: 10 * time.Second,
		NonVerbose: true,
	}
	ws.Dial(fmt.Sprintf(pathTemplate, scheme, pbURL.Host, outpostUUID.String()), header)

	ac.logger.WithField("outpost", outpostUUID.String()).Debug("connecting to passbook")

	ac.wsConn = ws
}

// Shutdown Gracefully stops all workers, disconnects from websocket
func (ac *APIController) Shutdown() {
	// Cleanly close the connection by sending a close message and then
	// waiting (with timeout) for the server to close the connection.
	err := ac.wsConn.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
	if err != nil {
		ac.logger.Println("write close:", err)
		return
	}
	return
}

func (ac *APIController) startWSHandler() {
	for {
		var wsMsg websocketMessage
		err := ac.wsConn.ReadJSON(&wsMsg)
		if err != nil {
			ac.logger.Println("read:", err)
			return
		}
		if wsMsg.Instruction != WebsocketInstructionAck {
			ac.logger.Debugf("%+v\n", wsMsg)
		}
		if wsMsg.Instruction == WebsocketInstructionTriggerUpdate {
			err := ac.UpdateIfRequired()
			if err != nil {
				ac.logger.WithError(err).Debug("Failed to update")
			}
		}
	}
}

func (ac *APIController) startWSHealth() {
	for ; true; <-time.Tick(time.Second * 10) {
		aliveMsg := websocketMessage{
			Instruction: WebsocketInstructionHello,
			Args:        make(map[string]interface{}),
		}
		err := ac.wsConn.WriteJSON(aliveMsg)
		if err != nil {
			ac.logger.Println("write:", err)
			return
		}
	}
}
