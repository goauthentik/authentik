package ak

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/go-openapi/strfmt"
	"github.com/gorilla/websocket"
	"github.com/recws-org/recws"
	pkg "goauthentik.io/internal/outpost"
)

func (ac *APIController) initWS(akURL url.URL, outpostUUID strfmt.UUID) {
	pathTemplate := "%s://%s/ws/outpost/%s/"
	scheme := strings.ReplaceAll(akURL.Scheme, "http", "ws")

	authHeader := fmt.Sprintf("Bearer %s", ac.token)

	header := http.Header{
		"Authorization": []string{authHeader},
		"User-Agent":    []string{pkg.UserAgent()},
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
	ws.Dial(fmt.Sprintf(pathTemplate, scheme, akURL.Host, outpostUUID.String()), header)

	ac.logger.WithField("logger", "authentik.outpost.ak-ws").WithField("outpost", outpostUUID.String()).Debug("connecting to authentik")

	ac.wsConn = ws
	// Send hello message with our version
	msg := websocketMessage{
		Instruction: WebsocketInstructionHello,
		Args: map[string]interface{}{
			"version":   pkg.VERSION,
			"buildHash": pkg.BUILD(),
			"uuid":      ac.instanceUUID.String(),
		},
	}
	err := ws.WriteJSON(msg)
	if err != nil {
		ac.logger.WithField("logger", "authentik.outpost.ak-ws").WithError(err).Warning("Failed to hello to authentik")
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
}

func (ac *APIController) startWSHandler() {
	logger := ac.logger.WithField("loop", "ws-handler")
	for {
		if !ac.wsConn.IsConnected() {
			continue
		}
		var wsMsg websocketMessage
		err := ac.wsConn.ReadJSON(&wsMsg)
		if err != nil {
			logger.WithError(err).Warning("ws write error, reconnecting")
			ac.wsConn.CloseAndReconnect()
			continue
		}
		if wsMsg.Instruction == WebsocketInstructionTriggerUpdate {
			time.Sleep(ac.reloadOffset)
			logger.Debug("Got update trigger...")
			err := ac.Server.Refresh()
			if err != nil {
				logger.WithError(err).Debug("Failed to update")
			}
		}
	}
}

func (ac *APIController) startWSHealth() {
	ticker := time.NewTicker(time.Second * 10)
	for ; true; <-ticker.C {
		if !ac.wsConn.IsConnected() {
			continue
		}
		aliveMsg := websocketMessage{
			Instruction: WebsocketInstructionHello,
			Args: map[string]interface{}{
				"version":   pkg.VERSION,
				"buildHash": pkg.BUILD(),
				"uuid":      ac.instanceUUID.String(),
			},
		}
		err := ac.wsConn.WriteJSON(aliveMsg)
		ac.logger.WithField("loop", "ws-health").Trace("hello'd")
		if err != nil {
			ac.logger.WithField("loop", "ws-health").WithError(err).Warning("ws write error, reconnecting")
			ac.wsConn.CloseAndReconnect()
			continue
		}
	}
}

func (ac *APIController) startIntervalUpdater() {
	logger := ac.logger.WithField("loop", "interval-updater")
	ticker := time.NewTicker(time.Second * 150)
	for ; true; <-ticker.C {
		err := ac.Server.Refresh()
		if err != nil {
			logger.WithError(err).Debug("Failed to update")
		}
	}
}
