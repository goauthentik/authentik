package ak

import (
	"context"
	"crypto/tls"
	"fmt"
	"maps"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/avast/retry-go/v4"
	"github.com/gorilla/websocket"
	"github.com/prometheus/client_golang/prometheus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
)

func (ac *APIController) getWebsocketURL(akURL url.URL, outpostUUID string, query url.Values) *url.URL {
	wsUrl := &url.URL{}
	wsUrl.Scheme = strings.ReplaceAll(akURL.Scheme, "http", "ws")
	wsUrl.Host = akURL.Host
	_p, _ := url.JoinPath(akURL.Path, "ws/outpost/", outpostUUID, "/")
	wsUrl.Path = _p
	v := url.Values{}
	maps.Insert(v, maps.All(akURL.Query()))
	maps.Insert(v, maps.All(query))
	wsUrl.RawQuery = v.Encode()
	return wsUrl
}

func (ac *APIController) initEvent(akURL url.URL, outpostUUID string) error {
	query := akURL.Query()
	query.Set("instance_uuid", ac.instanceUUID.String())

	authHeader := fmt.Sprintf("Bearer %s", ac.token)

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

	wsu := ac.getWebsocketURL(akURL, outpostUUID, query).String()
	ac.logger.WithField("url", wsu).Debug("connecting to websocket")
	ws, _, err := dialer.Dial(wsu, header)
	if err != nil {
		ac.logger.WithError(err).Warning("failed to connect websocket")
		return err
	}

	ac.eventConn = ws
	// Send hello message with our version
	msg := Event{
		Instruction: EventKindHello,
		Args:        ac.getEventPingArgs(),
	}
	err = ws.WriteJSON(msg)
	if err != nil {
		ac.logger.WithField("logger", "authentik.outpost.events").WithError(err).Warning("Failed to hello to authentik")
		return err
	}
	ac.lastWsReconnect = time.Now()
	ac.logger.WithField("logger", "authentik.outpost.events").WithField("outpost", outpostUUID).Info("Successfully connected websocket")
	return nil
}

// Shutdown Gracefully stops all workers, disconnects from websocket
func (ac *APIController) Shutdown() {
	// Cleanly close the connection by sending a close message and then
	// waiting (with timeout) for the server to close the connection.
	err := ac.eventConn.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
	if err != nil {
		ac.logger.WithError(err).Warning("failed to write close message")
		return
	}
	err = ac.eventConn.Close()
	if err != nil {
		ac.logger.WithError(err).Warning("failed to close websocket")
	}
	ac.logger.Info("finished shutdown")
}

func (ac *APIController) recentEvents() {
	if ac.wsIsReconnecting {
		return
	}
	ac.wsIsReconnecting = true
	u := url.URL{
		Host:   ac.Client.GetConfig().Host,
		Scheme: ac.Client.GetConfig().Scheme,
		Path:   strings.ReplaceAll(ac.Client.GetConfig().Servers[0].URL, "api/v3", ""),
	}
	attempt := 1
	_ = retry.Do(
		func() error {
			q := u.Query()
			q.Set("attempt", strconv.Itoa(attempt))
			u.RawQuery = q.Encode()
			err := ac.initEvent(u, ac.Outpost.Pk)
			attempt += 1
			if err != nil {
				return err
			}
			ac.wsIsReconnecting = false
			return nil
		},
		retry.Delay(1*time.Second),
		retry.MaxDelay(5*time.Minute),
		retry.DelayType(retry.BackOffDelay),
		retry.Attempts(0),
		retry.OnRetry(func(attempt uint, err error) {
			ac.logger.Infof("waiting %d seconds to reconnect", attempt)
		}),
	)
}

func (ac *APIController) startEventHandler() {
	logger := ac.logger.WithField("loop", "event-handler")
	for {
		var wsMsg Event
		if ac.eventConn == nil {
			go ac.recentEvents()
			time.Sleep(time.Second * 5)
			continue
		}
		err := ac.eventConn.ReadJSON(&wsMsg)
		if err != nil {
			ConnectionStatus.With(prometheus.Labels{
				"outpost_name": ac.Outpost.Name,
				"outpost_type": ac.Server.Type(),
				"uuid":         ac.instanceUUID.String(),
			}).Set(0)
			logger.WithError(err).Warning("event read error")
			go ac.recentEvents()
			time.Sleep(time.Second * 5)
			continue
		}
		ConnectionStatus.With(prometheus.Labels{
			"outpost_name": ac.Outpost.Name,
			"outpost_type": ac.Server.Type(),
			"uuid":         ac.instanceUUID.String(),
		}).Set(1)
		switch wsMsg.Instruction {
		case EventKindAck:
		case EventKindTriggerUpdate:
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
					"version":      constants.VERSION(),
					"build":        constants.BUILD(""),
				}).SetToCurrentTime()
			}
		default:
			for _, h := range ac.eventHandlers {
				err := h(context.Background(), wsMsg)
				if err != nil {
					ac.logger.WithError(err).Warning("failed to run event handler")
				}
			}
		}
	}
}

func (ac *APIController) startEventHealth() {
	ticker := time.NewTicker(time.Second * 10)
	for ; true; <-ticker.C {
		if ac.eventConn == nil {
			go ac.recentEvents()
			time.Sleep(time.Second * 5)
			continue
		}
		err := ac.SendEventHello(map[string]interface{}{})
		if err != nil {
			ac.logger.WithField("loop", "event-health").WithError(err).Warning("event write error")
			go ac.recentEvents()
			time.Sleep(time.Second * 5)
			continue
		} else {
			ac.logger.WithField("loop", "event-health").Trace("hello'd")
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
	getInterval := func() time.Duration {
		// Ensure timer interval is not negative or 0
		// for 0 we assume migration or unconfigured, so default to 5 minutes
		if ac.Outpost.RefreshIntervalS <= 0 {
			return 5 * time.Minute
		}
		// Clamp interval to be at least 30 seconds
		if ac.Outpost.RefreshIntervalS < 30 {
			return 30 * time.Second
		}
		return time.Duration(ac.Outpost.RefreshIntervalS) * time.Second
	}
	ticker := time.NewTicker(getInterval())
	for ; true; <-ticker.C {
		logger.Debug("Running interval update")
		err := ac.OnRefresh()
		if err != nil {
			logger.WithError(err).Debug("Failed to update")
		} else {
			LastUpdate.With(prometheus.Labels{
				"outpost_name": ac.Outpost.Name,
				"outpost_type": ac.Server.Type(),
				"uuid":         ac.instanceUUID.String(),
				"version":      constants.VERSION(),
				"build":        constants.BUILD(""),
			}).SetToCurrentTime()
		}
		ticker.Reset(getInterval())
	}
}

func (a *APIController) AddEventHandler(handler EventHandler) {
	a.eventHandlers = append(a.eventHandlers, handler)
}

func (a *APIController) SendEventHello(args map[string]interface{}) error {
	allArgs := a.getEventPingArgs()
	for key, value := range args {
		allArgs[key] = value
	}
	aliveMsg := Event{
		Instruction: EventKindHello,
		Args:        allArgs,
	}
	err := a.eventConn.WriteJSON(aliveMsg)
	return err
}
