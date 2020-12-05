package server

import (
	"crypto/tls"
	"encoding/base64"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/BeryJu/authentik/proxy/pkg"
	"github.com/go-openapi/strfmt"
	"github.com/gorilla/websocket"
	"github.com/recws-org/recws"
)

func (ac *APIController) initWS(pbURL url.URL, outpostUUID strfmt.UUID) {
	pathTemplate := "%s://%s/ws/outpost/%s/"
	scheme := strings.ReplaceAll(pbURL.Scheme, "http", "ws")

	authHeader := base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("Basic :%s", ac.token)))

	header := http.Header{
		"Authorization": []string{authHeader},
		"User-Agent":    []string{fmt.Sprintf("authentik-proxy@%s", pkg.VERSION)},
	}

	value, set := os.LookupEnv("AUTHENTIK_INSECURE")
	if !set {
		value = "false"
	}

	ws := &recws.RecConn{
		NonVerbose: true,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: strings.ToLower(value) == "true",
		},
	}
	ws.Dial(fmt.Sprintf(pathTemplate, scheme, pbURL.Host, outpostUUID.String()), header)

	ac.logger.WithField("component", "ws").WithField("outpost", outpostUUID.String()).Debug("connecting to authentik")

	ac.wsConn = ws
	// Send hello message with our version
	msg := websocketMessage{
		Instruction: WebsocketInstructionHello,
		Args: map[string]interface{}{
			"version": pkg.VERSION,
		},
	}
	err := ws.WriteJSON(msg)
	if err != nil {
		ac.logger.WithField("component", "ws").WithError(err).Warning("Failed to hello to authentik")
	}
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
	notConnectedBackoff := 1
	for {
		if !ac.wsConn.IsConnected() {
			notConnectedWait := time.Duration(notConnectedBackoff) * time.Second
			ac.logger.WithField("loop", "ws-handler").WithField("wait", notConnectedWait).Info("Not connected, trying again...")
			time.Sleep(notConnectedWait)
			notConnectedBackoff += notConnectedBackoff
			continue
		}
		var wsMsg websocketMessage
		err := ac.wsConn.ReadJSON(&wsMsg)
		if err != nil {
			ac.logger.WithField("loop", "ws-handler").Println("read:", err)
			ac.wsConn.CloseAndReconnect()
			continue
		}
		if wsMsg.Instruction == WebsocketInstructionTriggerUpdate {
			time.Sleep(ac.reloadOffset)
			err := ac.UpdateIfRequired()
			if err != nil {
				ac.logger.WithField("loop", "ws-handler").WithError(err).Debug("Failed to update")
			}
		}
	}
}

func (ac *APIController) startWSHealth() {
	for ; true; <-time.Tick(time.Second * 10) {
		if !ac.wsConn.IsConnected() {
			continue
		}
		aliveMsg := websocketMessage{
			Instruction: WebsocketInstructionHello,
			Args: map[string]interface{}{
				"version": pkg.VERSION,
			},
		}
		err := ac.wsConn.WriteJSON(aliveMsg)
		ac.logger.WithField("loop", "ws-health").Debug("hello'd")
		if err != nil {
			ac.logger.WithField("loop", "ws-health").Println("write:", err)
			ac.wsConn.CloseAndReconnect()
			continue
		}
	}
}
