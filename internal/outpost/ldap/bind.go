package ldap

import (
	"context"
	"net"
	"strings"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
)

type BindRequest struct {
	BindDN string
	BindPW string
	id     string
	conn   net.Conn
	log    *log.Entry
	ctx    context.Context
}

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	span := sentry.StartSpan(context.TODO(), "authentik.providers.ldap.bind",
		sentry.TransactionName("authentik.providers.ldap.bind"))
	rid := uuid.New().String()
	span.SetTag("request_uid", rid)
	span.SetTag("user.username", bindDN)
	defer span.Finish()

	bindDN = strings.ToLower(bindDN)
	req := BindRequest{
		BindDN: bindDN,
		BindPW: bindPW,
		conn:   conn,
		log:    ls.log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", conn.RemoteAddr().String()),
		id:     rid,
		ctx:    span.Context(),
	}
	req.log.Info("Bind request")
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, req)
		} else {
			ls.log.WithError(err).Debug("Username not for instance")
		}
	}
	req.log.WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}

func (ls *LDAPServer) TimerFlowCacheExpiry() {
	for _, p := range ls.providers {
		ls.log.WithField("flow", p.flowSlug).Debug("Pre-heating flow cache")
		p.TimerFlowCacheExpiry()
	}
}
