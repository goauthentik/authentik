package ak

type WebsocketInstruction int

const (
	// WebsocketInstructionAck Code used to acknowledge a previous message
	WebsocketInstructionAck WebsocketInstruction = 0
	// WebsocketInstructionHello Code used to send a healthcheck keepalive
	WebsocketInstructionHello WebsocketInstruction = 1
	// WebsocketInstructionTriggerUpdate Code received to trigger a config update
	WebsocketInstructionTriggerUpdate WebsocketInstruction = 2
	// WebsocketInstructionProviderSpecific Code received to trigger some provider specific function
	WebsocketInstructionProviderSpecific WebsocketInstruction = 3
)

type websocketMessage struct {
	Instruction WebsocketInstruction   `json:"instruction"`
	Args        map[string]interface{} `json:"args"`
}
