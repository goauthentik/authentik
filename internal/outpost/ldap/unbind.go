package ldap

import (
	"net"

	"github.com/getsentry/sentry-go"
	"beryju.io/ldap"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/metrics"
)

func (ls *LDAPServer) Unbind(boundDN string, conn net.Conn) (ldap.LDAPResultCode, error) {
	req, span := bind.NewRequest(boundDN, "", conn)
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": ls.ac.Outpost.Name,
			"type":         "unbind",
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)))
		req.Log().WithField("took-ms", span.EndTime.Sub(span.StartTime).Milliseconds()).Info("Unbind request")
	}()

	defer func() {
		err := recover()
		if err == nil {
			return
		}
		log.WithError(err.(error)).Error("recover in bind request")
		sentry.CaptureException(err.(error))
	}()

	for _, instance := range ls.providers {
		username, err := instance.binder.GetUsername(boundDN)
		if err == nil {
			selectedApp = instance.GetAppSlug()
			return instance.binder.Unbind(username, req)
		} else {
			req.Log().WithError(err).Debug("Username not for instance")
		}
	}
	req.Log().WithField("request", "unbind").Warning("No provider found for request")
	metrics.RequestsRejected.With(prometheus.Labels{
		"outpost_name": ls.ac.Outpost.Name,
		"type":         "unbind",
		"reason":       "no_provider",
		"app":          "",
	}).Inc()
	return ldap.LDAPResultOperationsError, nil
}
