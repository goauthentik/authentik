package protocol

import (
	"errors"
	"slices"
)

type StateManager interface {
	GetEAPSettings() Settings
	GetEAPState(string) *State
	SetEAPState(string, *State)
}

type ProtocolConstructor func() Payload

type Settings struct {
	Protocols        []ProtocolConstructor
	ProtocolPriority []Type
	ProtocolSettings map[Type]interface{}
}

type State struct {
	Protocols        []ProtocolConstructor
	ProtocolIndex    int
	ProtocolPriority []Type
	TypeState        map[Type]any
}

func (st *State) GetNextProtocol() (Type, error) {
	if st.ProtocolIndex >= len(st.ProtocolPriority) {
		return Type(0), errors.New("no more protocols to offer")
	}
	return st.ProtocolPriority[st.ProtocolIndex], nil
}

func BlankState(settings Settings) *State {
	return &State{
		Protocols:        slices.Clone(settings.Protocols),
		ProtocolPriority: slices.Clone(settings.ProtocolPriority),
		TypeState:        map[Type]any{},
	}
}
