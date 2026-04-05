package radius

import (
	"encoding/base64"
	"errors"

	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/radius/metrics"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
)

func (rs *RadiusServer) Handle_AccessRequest_PAP_Auth(r *RadiusRequest, username, password string) (*radius.Packet, error) {
	fe := flow.NewFlowExecutor(r.Context(), r.pi.flowSlug, r.pi.s.ac.Client.GetConfig(), log.Fields{
		"username":  username,
		"client":    r.RemoteAddr(),
		"requestId": r.ID(),
	})
	fe.DelegateClientIP(r.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/radius", "true")

	fe.Answers[flow.StageIdentification] = username
	fe.SetSecrets(password, r.pi.MFASupport)

	passed, err := fe.Execute()
	if err != nil {
		r.Log().WithField("username", username).WithError(err).Warning("failed to execute flow")
		return nil, errors.New("flow_error")
	}
	if !passed {
		return nil, errors.New("invalid_credentials")
	}
	access, _, err := fe.ApiClient().OutpostsAPI.OutpostsRadiusAccessCheck(
		r.Context(), r.pi.providerId,
	).AppSlug(r.pi.appSlug).Execute()
	if err != nil {
		r.Log().WithField("username", username).WithError(err).Warning("failed to check access")
		return nil, errors.New("access_check_fail")
	}
	if !access.Access.Passing {
		r.Log().WithField("username", username).Info("Access denied for user")
		return nil, errors.New("access_denied")
	}
	res := r.Response(radius.CodeAccessAccept)
	if !access.HasAttributes() {
		r.Log().Debug("No attributes")
		return res, nil
	}
	rawData, err := base64.StdEncoding.DecodeString(access.GetAttributes())
	if err != nil {
		r.Log().WithError(err).Warning("failed to decode attributes from core")
		return nil, errors.New("attribute_decode_failed")
	}
	p, err := radius.Parse(rawData, r.pi.SharedSecret)
	if err != nil {
		r.Log().WithError(err).Warning("failed to parse attributes from core")
		return nil, errors.New("attribute_parse_failed")
	}
	for _, attr := range p.Attributes {
		res.Add(attr.Type, attr.Attribute)
	}
	return res, nil
}

func (rs *RadiusServer) Handle_AccessRequest_PAP(w radius.ResponseWriter, r *RadiusRequest) {
	username := rfc2865.UserName_GetString(r.Packet)
	password := rfc2865.UserPassword_GetString(r.Packet)
	res, err := rs.Handle_AccessRequest_PAP_Auth(r, username, password)
	if err != nil {
		metrics.RequestsRejected.With(prometheus.Labels{
			"outpost_name": rs.ac.Outpost.Name,
			"reason":       err.Error(),
			"app":          r.pi.appSlug,
		}).Inc()
		_ = w.Write(r.Reject())
		return
	}
	err = r.setMessageAuthenticator(res)
	if err != nil {
		rs.log.WithError(err).Warning("failed to set message authenticator")
	}
	_ = w.Write(res)
}
