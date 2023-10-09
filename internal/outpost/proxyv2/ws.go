package proxyv2

import (
	"context"

	"github.com/mitchellh/mapstructure"
	"goauthentik.io/internal/outpost/proxyv2/application"
)

type WSProviderSubType string

const (
	WSProviderSubTypeLogout WSProviderSubType = "logout"
)

type WSProviderMsg struct {
	SubType   WSProviderSubType `mapstructure:"sub_type"`
	SessionID string            `mapstructure:"session_id"`
}

func ParseWSProvider(args map[string]interface{}) (*WSProviderMsg, error) {
	msg := &WSProviderMsg{}
	err := mapstructure.Decode(args, &msg)
	if err != nil {
		return nil, err
	}
	return msg, nil
}

func (ps *ProxyServer) handleWSMessage(ctx context.Context, args map[string]interface{}) {
	msg, err := ParseWSProvider(args)
	if err != nil {
		ps.log.WithError(err).Warning("invalid provider-specific ws message")
		return
	}
	switch msg.SubType {
	case WSProviderSubTypeLogout:
		for _, p := range ps.apps {
			err := p.Logout(ctx, func(c application.Claims) bool {
				return c.Sid == msg.SessionID
			})
			if err != nil {
				ps.log.WithField("provider", p.Host).WithError(err).Warning("failed to logout")
			}
		}
	default:
		ps.log.WithField("sub_type", msg.SubType).Warning("invalid sub_type")
	}
}
