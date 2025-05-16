package eap

import (
	"slices"

	"goauthentik.io/internal/outpost/radius/eap/protocol"
)

type Settings struct {
	ProtocolsToOffer []protocol.Type
	ProtocolSettings map[protocol.Type]interface{}
}

type StateManager interface {
	GetEAPSettings() Settings
	GetEAPState(string) *State
	SetEAPState(string, *State)
}

type State struct {
	ChallengesToOffer []protocol.Type
	TypeState         map[protocol.Type]any
}

func BlankState(settings Settings) *State {
	return &State{
		ChallengesToOffer: slices.Clone(settings.ProtocolsToOffer),
		TypeState:         map[protocol.Type]any{},
	}
}
