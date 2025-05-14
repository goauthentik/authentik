package eap

import "slices"

type Settings struct {
	ChallengesToOffer []Type
	ChallengeSettings map[Type]interface{}
}

type StateManager interface {
	GetEAPSettings() Settings
	GetEAPState(string) *State
	SetEAPState(string, *State)
}

type State struct {
	ChallengesToOffer []Type
	TypeState         map[Type]any
}

func BlankState(settings Settings) *State {
	return &State{
		ChallengesToOffer: slices.Clone(settings.ChallengesToOffer),
		TypeState:         map[Type]any{},
	}
}
