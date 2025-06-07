package radius

import (
	"encoding/base64"

	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
)

func (rs *RadiusServer) Handle_AccessRequest(w radius.ResponseWriter, r *RadiusRequest) {
	username := rfc2865.UserName_GetString(r.Packet)

	fe := flow.NewFlowExecutor(r.Context(), r.pi.flowSlug, r.pi.s.ac.Client.GetConfig(), log.Fields{
		"username":  username,
		"client":    r.RemoteAddr(),
		"requestId": r.ID(),
	})
	fe.DelegateClientIP(r.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/radius", "true")

	fe.Answers[flow.StageIdentification] = username
	fe.SetSecrets(rfc2865.UserPassword_GetString(r.Packet), r.pi.MFASupport)

	passed, err := fe.Execute()
	if err != nil {
		r.Log().WithField("username", username).WithError(err).Warning("failed to execute flow")
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "flow_error",
			"app":          r.pi.appSlug,
		}).Inc()
		_ = w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	if !passed {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "invalid_credentials",
			"app":          r.pi.appSlug,
		}).Inc()
		_ = w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	access, _, err := fe.ApiClient().OutpostsApi.OutpostsRadiusAccessCheck(
		r.Context(), r.pi.providerId,
	).AppSlug(r.pi.appSlug).Execute()
	if err != nil {
		r.Log().WithField("username", username).WithError(err).Warning("failed to check access")
		_ = w.Write(r.Response(radius.CodeAccessReject))
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "access_check_fail",
			"app":          r.pi.appSlug,
		}).Inc()
		return
	}
	if !access.Access.Passing {
		r.Log().WithField("username", username).Info("Access denied for user")
		_ = w.Write(r.Response(radius.CodeAccessReject))
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "access_denied",
			"app":          r.pi.appSlug,
		}).Inc()
		return
	}
	res := r.Response(radius.CodeAccessAccept)
	defer func() { _ = w.Write(res) }()
	if !access.HasAttributes() {
		r.Log().Debug("No attributes")
		return
	}
	rawData, err := base64.StdEncoding.DecodeString(access.GetAttributes())
	if err != nil {
		r.Log().WithError(err).Warning("failed to decode attributes from core")
		return
	}
	p, err := radius.Parse(rawData, r.pi.SharedSecret)
	if err != nil {
		r.Log().WithError(err).Warning("failed to parse attributes from core")
	}
	for _, attr := range p.Attributes {
		res.Add(attr.Type, attr.Attribute)
	}
}
