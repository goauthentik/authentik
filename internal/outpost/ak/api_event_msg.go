package ak

import (
	"context"

	"github.com/mitchellh/mapstructure"
)

type EventKind int

const (
	// Code used to acknowledge a previous message
	EventKindAck EventKind = 0
	// Code used to send a healthcheck keepalive
	EventKindHello EventKind = 1
	// Code received to trigger a config update
	EventKindTriggerUpdate EventKind = 2
	// Code received to trigger some provider specific function
	EventKindProviderSpecific EventKind = 3
	// Code received to identify the end of a session
	EventKindSessionEnd EventKind = 4
)

type EventHandler func(ctx context.Context, msg Event) error

type Event struct {
	Instruction EventKind   `json:"instruction"`
	Args        interface{} `json:"args"`
}

func (wm Event) ArgsAs(out interface{}) error {
	return mapstructure.Decode(wm.Args, out)
}

type EventArgsSessionEnd struct {
	SessionID string `mapstructure:"session_id"`
}
