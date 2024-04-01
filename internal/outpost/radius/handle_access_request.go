package radius

import (
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/rfc2866"
)

func (rs *RadiusServer) Handle_AccessRequest(w radius.ResponseWriter, r *RadiusRequest) {
	username := rfc2865.UserName_GetString(r.Packet)

	fe := flow.NewFlowExecutor(r.Context(), r.pi.authenticationFlowSlug, r.pi.s.ac.Client.GetConfig(), log.Fields{
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
	access, err := fe.CheckApplicationAccess(r.pi.appSlug)
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
	if !access {
		r.Log().WithField("username", username).Info("Access denied for user")
		_ = w.Write(r.Response(radius.CodeAccessReject))
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       "access_denied",
			"app":          r.pi.appSlug,
		}).Inc()
		return
	}
	// Get user info to store in context
	userInfo, _, err := fe.ApiClient().CoreApi.CoreUsersMeRetrieve(r.Context()).Execute()
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"type":         "bind",
			"reason":       "user_info_fail",
		}).Inc()
		r.Log().WithError(err).Warning("failed to get user info")
		return
	}

	response := r.Response(radius.CodeAccessAccept)
	_ = rfc2866.AcctSessionID_SetString(response, fe.GetSession().String())
	r.pi.boundUsersMutex.Lock()
	r.pi.boundUsers[fe.GetSession().String()] = &flags.UserFlags{
		Session: fe.GetSession(),
		UserPk:  userInfo.Original.Pk,
	}
	r.pi.boundUsersMutex.Unlock()
	err = w.Write(response)
	if err != nil {
		r.Log().WithError(err).Warning("failed to write response")
	}
}
