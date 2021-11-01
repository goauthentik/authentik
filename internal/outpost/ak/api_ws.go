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
	"github.com/prometheus/client_golang/prometheus"
	"github.com/recws-org/recws"
	"goauthentik.io/internal/constants"
)

func (ac *APIController) initWS(akURL url.URL, outpostUUID strfmt.UUID) {
	pathTemplate := "%s://%s/ws/outpost/%s/"
	scheme := strings.ReplaceAll(akURL.Scheme, "http", "ws")

	authHeader := fmt.Sprintf("Bearer %s", ac.token)

	header := http.Header{
		"Authorization": []string{authHeader},
		"User-Agent":    []string{constants.OutpostUserAgent()},
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

	ac.logger.WithField("logger", "authentik.outpost.ak-ws").WithField("outpost", outpostUUID.String()).Debug("Connecting to authentik")

	ac.wsConn = ws
	// Send hello message with our version
	msg := websocketMessage{
		Instruction: WebsocketInstructionHello,
		Args: map[string]interface{}{
			"version":   constants.VERSION,
			"buildHash": constants.BUILD(),
			"uuid":      ac.instanceUUID.String(),
		},
	}
	err := ws.WriteJSON(msg)
	if err != nil {
		ac.logger.WithField("logger", "authentik.outpost.ak-ws").WithError(err).Warning("Failed to hello to authentik")
	}
	ac.lastWsReconnect = time.Now()
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

func (ac *APIController) startWSReConnector() {
	for {
		time.Sleep(time.Second * 5)
		if ac.wsConn.IsConnected() {
			continue
		}
		if time.Since(ac.lastWsReconnect).Seconds() > 30 {
			ac.wsConn.CloseAndReconnect()
			ac.logger.Info("Reconnecting websocket")
			ac.lastWsReconnect = time.Now()
		}
	}
}

func (ac *APIController) startWSHandler() {
	logger := ac.logger.WithField("loop", "ws-handler")
	for {
		var wsMsg websocketMessage
		err := ac.wsConn.ReadJSON(&wsMsg)
		if err != nil {
			ConnectionStatus.With(prometheus.Labels{
				"outpost_name": ac.Outpost.Name,
				"outpost_type": ac.Server.Type(),
				"uuid":         ac.instanceUUID.String(),
			}).Set(0)
			logger.WithError(err).Warning("ws read error")
			time.Sleep(time.Second * 5)
			continue
		}
		ConnectionStatus.With(prometheus.Labels{
			"outpost_name": ac.Outpost.Name,
			"outpost_type": ac.Server.Type(),
			"uuid":         ac.instanceUUID.String(),
		}).Set(1)
		if wsMsg.Instruction == WebsocketInstructionTriggerUpdate {
			time.Sleep(ac.reloadOffset)
			logger.Debug("Got update trigger...")
			err := ac.OnRefresh()
			if err != nil {
				logger.WithError(err).Debug("Failed to update")
			} else {
				LastUpdate.With(prometheus.Labels{
					"outpost_name": ac.Outpost.Name,
					"outpost_type": ac.Server.Type(),
					"uuid":         ac.instanceUUID.String(),
					"version":      constants.VERSION,
					"build":        constants.BUILD(),
				}).SetToCurrentTime()
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
				"version":   constants.VERSION,
				"buildHash": constants.BUILD(),
				"uuid":      ac.instanceUUID.String(),
			},
		}
		err := ac.wsConn.WriteJSON(aliveMsg)
		ac.logger.WithField("loop", "ws-health").Trace("hello'd")
		if err != nil {
			ac.logger.WithField("loop", "ws-health").WithError(err).Warning("ws write error")
			time.Sleep(time.Second * 5)
			continue
		} else {
			ConnectionStatus.With(prometheus.Labels{
				"outpost_name": ac.Outpost.Name,
				"outpost_type": ac.Server.Type(),
				"uuid":         ac.instanceUUID.String(),
			}).Set(1)
		}
	}
}

func (ac *APIController) startIntervalUpdater() {
	logger := ac.logger.WithField("loop", "interval-updater")
	ticker := time.NewTicker(5 * time.Minute)
	for ; true; <-ticker.C {
		err := ac.OnRefresh()
		if err != nil {
			logger.WithError(err).Debug("Failed to update")
		} else {
			LastUpdate.With(prometheus.Labels{
				"outpost_name": ac.Outpost.Name,
				"outpost_type": ac.Server.Type(),
				"uuid":         ac.instanceUUID.String(),
				"version":      constants.VERSION,
				"build":        constants.BUILD(),
			}).SetToCurrentTime()
		}
	}
}
