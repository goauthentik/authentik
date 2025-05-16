package eap

import (
	"github.com/sirupsen/logrus"
	"layeh.com/radius"
)

type context[TState any, TSettings any] struct {
}

func (ctx context[TState, TSettings]) ProtocolSettings() TSettings {
	return 0
}

func (ctx context[TState, TSettings]) GetProtocolState(def func(context[TState, TSettings]) TState) TState {
	return nil
}

func (ctx context[TState, TSettings]) SetProtocolState(TState) {

}

func (ctx context[TState, TSettings]) EndInnerProtocol(func(p *radius.Packet) *radius.Packet) {

}

func (ctx context[TState, TSettings]) Log() *logrus.Entry {
	return nil
}
