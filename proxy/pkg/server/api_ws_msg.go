package server

type WebsocketInstruction int

const (
	WebsocketInstructionAck           WebsocketInstruction = 0
	WebsocketInstructionHello         WebsocketInstruction = 1
	WebsocketInstructionTriggerUpdate WebsocketInstruction = 2
)

type WebsocketMessage struct {
	Instruction WebsocketInstruction   `json:"instruction"`
	Args        map[string]interface{} `json:"args"`
}
