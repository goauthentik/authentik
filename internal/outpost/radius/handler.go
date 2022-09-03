package radius

import (
	"context"

	"github.com/getsentry/sentry-go"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"

	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
)

func (rs RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	span := sentry.StartSpan(context.TODO(), "authentik.providers.radius.connect",
		sentry.TransactionName("authentik.providers.radius.connect"))
	selectedApp := ""
	defer func() {
		span.Finish()
		metrics.Requests.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"app":          selectedApp,
		}).Observe(float64(span.EndTime.Sub(span.StartTime)))
	}()

	rs.log.WithField("code", r.Code).Debug("Radius Request")
	var pi *ProviderInstance
	for _, p := range rs.providers {
		if string(p.SharedSecret) == string(r.Secret) {
			pi = p
			break
		}
	}

	username := rfc2865.UserName_GetString(r.Packet)

	fe := flow.NewFlowExecutor(r.Context(), pi.flowSlug, pi.s.ac.Client.GetConfig(), log.Fields{
		"username": username,
		"client":   r.RemoteAddr.String(),
	})
	fe.DelegateClientIP(r.RemoteAddr.String())
	fe.Params.Add("goauthentik.io/outpost/radius", "true")

	fe.Answers[flow.StageIdentification] = username
	fe.Answers[flow.StagePassword] = rfc2865.UserPassword_GetString(r.Packet)

	passed, err := fe.Execute()

	if err != nil {
		pi.log.WithField("username", username).WithError(err).Warning("failed to execute flow")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "flow_error",
			"app":          selectedApp,
		}).Inc()
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	if !passed {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "invalid_credentials",
			"app":          selectedApp,
		}).Inc()
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	access, err := fe.CheckApplicationAccess(pi.appSlug)
	if err != nil {
		pi.log.WithField("username", username).WithError(err).Warning("failed to check access")
		w.Write(r.Response(radius.CodeAccessReject))
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "access_check_fail",
			"app":          selectedApp,
		}).Inc()
		return
	}
	if !access {
		pi.log.WithField("username", username).Info("Access denied for user")
		w.Write(r.Response(radius.CodeAccessReject))
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "access_denied",
			"app":          selectedApp,
		}).Inc()
		return
	}
	w.Write(r.Response(radius.CodeAccessAccept))
}
