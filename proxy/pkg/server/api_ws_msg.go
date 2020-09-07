package server

type websocketInstruction int

const (
	// WebsocketInstructionAck Code used to acknowledge a previous message
	WebsocketInstructionAck websocketInstruction = 0
	// WebsocketInstructionHello Code used to send a healthcheck keepalive
	WebsocketInstructionHello websocketInstruction = 1
	// WebsocketInstructionTriggerUpdate Code received to trigger a config update
	WebsocketInstructionTriggerUpdate websocketInstruction = 2
)

type websocketMessage struct {
	Instruction websocketInstruction   `json:"instruction"`
	Args        map[string]interface{} `json:"args"`
}
