package radius

import (
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/ldap/flags"
	"layeh.com/radius"
	"layeh.com/radius/rfc2866"
)

func (rs *RadiusServer) Handle_DisconnectRequest(w radius.ResponseWriter, r *RadiusRequest) {
	session := rfc2866.AcctSessionID_GetString(r.Packet)

	sendFailResponse := func() {
		failResponse := r.Response(radius.CodeDisconnectACK)
		err := w.Write(failResponse)
		if err != nil {
			r.Log().WithError(err).Warning("failed to write response")
		}
	}

	r.pi.boundUsersMutex.Lock()
	var f *flags.UserFlags
	if ff, ok := r.pi.boundUsers[session]; !ok {
		r.pi.boundUsersMutex.Unlock()
		sendFailResponse()
		return
	} else {
		f = ff
	}
	r.pi.boundUsersMutex.Unlock()

	fe := flow.NewFlowExecutor(r.Context(), r.pi.invalidationFlowSlug, rs.ac.Client.GetConfig(), log.Fields{
		"client":    r.RemoteAddr(),
		"requestId": r.ID(),
	})
	fe.SetSession(f.Session)
	fe.DelegateClientIP(r.RemoteAddr())
	fe.Params.Add("goauthentik.io/outpost/radius", "true")
	_, err := fe.Execute()
	if err != nil {
		r.log.WithError(err).Warning("failed to logout user")
		sendFailResponse()
		return
	}
	r.pi.boundUsersMutex.Lock()
	delete(r.pi.boundUsers, session)
	r.pi.boundUsersMutex.Unlock()
	response := r.Response(radius.CodeDisconnectACK)
	err = w.Write(response)
	if err != nil {
		r.Log().WithError(err).Warning("failed to write response")
	}
}
