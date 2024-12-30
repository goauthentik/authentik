package proxyv2

import (
	"context"

	"github.com/mitchellh/mapstructure"
	"go.uber.org/zap"
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
		ps.log.Warn("invalid provider-specific ws message", zap.Error(err))
		return
	}
	switch msg.SubType {
	case WSProviderSubTypeLogout:
		for _, p := range ps.apps {
			ps.log.Debug("Logging out", zap.String("provider", p.Host))
			err := p.Logout(ctx, func(c application.Claims) bool {
				return c.Sid == msg.SessionID
			})
			if err != nil {
				ps.log.Warn("failed to logout", zap.String("provider", p.Host), zap.Error(err))
			}
		}
	default:
		ps.log.Warn("invalid sub_type", zap.String("sub_type", string(msg.SubType)))
	}
}
