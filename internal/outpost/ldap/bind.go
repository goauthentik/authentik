package ldap

import (
	"net"
	"time"

	"beryju.io/ldap"
	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	"go.uber.org/zap"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/metrics"
)

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	req, span := bind.NewRequest(bindDN, bindPW, conn)
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": ls.ac.Outpost.Name,
			"type":         "bind",
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)) / float64(time.Second))
		req.Log().Info("Bind request", zap.Duration("took-ms", span.EndTime.Sub(span.StartTime)))
	}()

	defer func() {
		err := recover()
		if err == nil {
			return
		}
		req.Log().Error("recover in bind request", zap.Error(err.(error)))
		sentry.CaptureException(err.(error))
	}()

	for _, instance := range ls.providers {
		username, err := instance.binder.GetUsername(bindDN)
		if err == nil {
			selectedApp = instance.GetAppSlug()
			return instance.binder.Bind(username, req)
		} else {
			req.Log().Debug("Username not for instance", zap.Error(err))
		}
	}
	req.Log().Warn("No provider found for request", zap.String("request", "bind"))
	metrics.RequestsRejected.With(prometheus.Labels{
		"outpost_name": ls.ac.Outpost.Name,
		"type":         "bind",
		"reason":       "no_provider",
		"app":          "",
	}).Inc()

	return ldap.LDAPResultInsufficientAccessRights, nil
}
