package radius

import (
	"goauthentik.io/internal/outpost"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
)

func (rs RadiusServer) ServeRADIUS(w radius.ResponseWriter, r *radius.Request) {
	rs.log.WithField("code", r.Code).Debug("Radius Request")
	var pi *ProviderInstance
	for _, p := range rs.providers {
		if string(p.SharedSecret) == string(r.Secret) {
			pi = p
			break
		}
	}

	fe := outpost.NewFlowExecutor(pi.flowSlug, pi.s.ac.Client.GetConfig())
	fe.DelegateClientIP(r.RemoteAddr)
	fe.Params.Add("goauthentik.io/outpost/radius", "true")

	username := rfc2865.UserName_GetString(r.Packet)
	fe.Answers[outpost.StageIdentification] = username
	fe.Answers[outpost.StagePassword] = rfc2865.UserPassword_GetString(r.Packet)

	passed, err := fe.Execute()

	if err != nil {
		pi.log.WithField("username", username).WithError(err).Warning("failed to execute flow")
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	if !passed {
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	access, err := fe.CheckApplicationAccess(pi.appSlug)
	if !access {
		pi.log.WithField("username", username).Info("Access denied for user")
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	if err != nil {
		pi.log.WithField("username", username).WithError(err).Warning("failed to check access")
		w.Write(r.Response(radius.CodeAccessReject))
		return
	}
	w.Write(r.Response(radius.CodeAccessAccept))
}
