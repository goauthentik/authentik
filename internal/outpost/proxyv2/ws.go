package proxyv2

import (
	"context"
	"crypto/sha256"
	"encoding/hex"

	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/proxyv2/application"
)

// hashSessionKey hashes the session key to match the format sent from the backend
func hashSessionKey(sessionKey string) string {
	h := sha256.Sum256([]byte(sessionKey))
	return hex.EncodeToString(h[:])
}

func (ps *ProxyServer) handleWSMessage(ctx context.Context, msg ak.Event) error {
	if msg.Instruction != ak.EventKindSessionEnd {
		return nil
	}
	mmsg := ak.EventArgsSessionEnd{}
	err := msg.ArgsAs(&mmsg)
	if err != nil {
		return err
	}

	ps.log.WithField("session_id", mmsg.SessionID).Info("Received session end event")

	for _, p := range ps.apps {
		ps.log.WithField("provider", p.Host).Debug("Logging out")
		err := p.Logout(ctx, func(c application.Claims) bool {
			hashedClaimsSid := hashSessionKey(c.Sid)
			match := hashedClaimsSid == mmsg.SessionID
			ps.log.WithField("provider", p.Host).WithField("claims_sid", c.Sid).WithField("hashed_claims_sid", hashedClaimsSid).WithField("message_session_id", mmsg.SessionID).WithField("match", match).Debug("Comparing session IDs for logout")
			return match
		})
		if err != nil {
			ps.log.WithField("provider", p.Host).WithError(err).Warning("failed to logout")
		}
	}
	return nil
}
