package eap

import (
	"errors"
	"slices"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

type ProtocolConstructor func() protocol.Payload

type Settings struct {
	Protocols        []ProtocolConstructor
	ProtocolPriority []protocol.Type
	ProtocolSettings map[protocol.Type]interface{}
}

type StateManager interface {
	GetEAPSettings() Settings
	GetEAPState(string) *State
	SetEAPState(string, *State)
}

type State struct {
	Protocols        []ProtocolConstructor
	ProtocolIndex    int
	ProtocolPriority []protocol.Type
	TypeState        map[protocol.Type]any
}

func (st *State) GetNextProtocol() (protocol.Type, error) {
	if st.ProtocolIndex >= len(st.ProtocolPriority) {
		return protocol.Type(0), errors.New("no more protocols to offer")
	}
	return st.ProtocolPriority[st.ProtocolIndex], nil
}

func BlankState(settings Settings) *State {
	return &State{
		Protocols:        slices.Clone(settings.Protocols),
		ProtocolPriority: slices.Clone(settings.ProtocolPriority),
		TypeState:        map[protocol.Type]any{},
	}
}
