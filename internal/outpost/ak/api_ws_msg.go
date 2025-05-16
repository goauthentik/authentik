package ak

import (
	"context"

	"github.com/mitchellh/mapstructure"
)

type WebsocketInstruction int

const (
	// Code used to acknowledge a previous message
	WebsocketInstructionAck WebsocketInstruction = 0
	// Code used to send a healthcheck keepalive
	WebsocketInstructionHello WebsocketInstruction = 1
	// Code received to trigger a config update
	WebsocketInstructionTriggerUpdate WebsocketInstruction = 2
	// Code received to trigger some provider specific function
	WebsocketInstructionProviderSpecific WebsocketInstruction = 3
	// Code received to identify the end of a session
	WebsocketInstructionSessionEnd WebsocketInstruction = 4
)

type WSHandler func(ctx context.Context, msg WebsocketMessage) error

type WebsocketMessage struct {
	Instruction WebsocketInstruction `json:"instruction"`
	Args        interface{}          `json:"args"`
}

func (wm WebsocketMessage) ArgsAs(out interface{}) error {
	return mapstructure.Decode(wm.Args, &out)
}

type WebsocketMessageSessionEnd struct {
	SessionID string `mapstructure:"session_id"`
}
