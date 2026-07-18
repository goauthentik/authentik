package proxyv2

import (
	"context"

	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/types"
)

func (ps *ProxyServer) handleWSMessage(ctx context.Context, msg ak.Event) error {
	if msg.Instruction != ak.EventKindSessionEnd {
		return nil
	}
	mmsg := ak.EventArgsSessionEnd{}
	err := msg.ArgsAs(&mmsg)
	if err != nil {
		return err
	}
	for _, p := range ps.apps {
		ps.log.WithField("provider", p.Host).Debug("Logging out")
		err := p.Logout(ctx, func(c types.Claims) bool {
			return c.Sid == mmsg.SessionID
		})
		if err != nil {
			ps.log.WithField("provider", p.Host).WithError(err).Warning("failed to logout")
		}
	}
	return nil
}
