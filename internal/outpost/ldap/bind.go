package ldap

import (
	"context"
	"net"
	"strings"

	"github.com/getsentry/sentry-go"
	"github.com/google/uuid"
	"github.com/nmcclain/ldap"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/metrics"
	"goauthentik.io/internal/utils"
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

	bindDN = strings.ToLower(bindDN)
	req := BindRequest{
		BindDN: bindDN,
		BindPW: bindPW,
		conn:   conn,
		log:    ls.log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", utils.GetIP(conn.RemoteAddr())),
		id:     rid,
		ctx:    span.Context(),
	}
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": ls.ac.Outpost.Name,
			"type":         "bind",
			"filter":       "",
			"dn":           req.BindDN,
			"client":       utils.GetIP(req.conn.RemoteAddr()),
		}).Observe(float64(span.EndTime.Sub(span.StartTime)))
		req.log.WithField("took-ms", span.EndTime.Sub(span.StartTime).Milliseconds()).Info("Bind request")
	}()
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, req)
		} else {
			req.log.WithError(err).Debug("Username not for instance")
		}
	}
	req.log.WithField("request", "bind").Warning("No provider found for request")
	metrics.RequestsRejected.With(prometheus.Labels{
		"outpost_name": ls.ac.Outpost.Name,
		"type":         "bind",
		"reason":       "no_provider",
		"dn":           bindDN,
		"client":       utils.GetIP(conn.RemoteAddr()),
	}).Inc()
	return ldap.LDAPResultOperationsError, nil
}

func (ls *LDAPServer) TimerFlowCacheExpiry() {
	for _, p := range ls.providers {
		ls.log.WithField("flow", p.flowSlug).Debug("Pre-heating flow cache")
		p.TimerFlowCacheExpiry()
	}
}
