package radius

import (
	"goauthentik.io/internal/outpost"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/rfc2869"
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

	if password, err := rfc2865.UserPassword_LookupString(r.Packet); err != nil && password != "" {
		rs.log.Debug("Got regular password")
		fe.Answers[outpost.StagePassword] = password
	} else {
		rs.log.Debug("Got eap message password")
		eap, err := rfc2869.EAPMessage_Lookup(r.Packet)
		if err != nil || len(eap) < 1 {
			// Neither plain password nor EAP, abort
			w.Write(r.Response(radius.CodeAccessReject))
			return
		}
		rs.log.WithField("eap-code", eap[0]).Debug(eap)
		// [2 125 0 6 1 106]
		// Create an EAP Request  / MD5 challenge
		er := []byte{
			EAPMessageCodeRequest,      // Code
			eap[1],                     // ID
			0,                          // Length
			0,                          // Length
			EAPMessageTypeMD5Challenge, // type
		} // + Payload
	}

	rs.log.Debug(rfc2865.UserPassword_GetString(r.Packet))
	rs.log.Debug()
	rs.log.Debug(rfc2869.MessageAuthenticator_GetString(r.Packet))

	// for _, attr := range r.Packet.Attributes {
	// 	rs.log.WithField("id", attr.Type).WithField("value", attr.Attribute).WithField("sv", string(attr.Attribute)).Debug("attr")
	// }

	// passed, err := fe.Execute()

	// if err != nil {
	// 	pi.log.WithField("username", username).WithError(err).Warning("failed to execute flow")
	// 	w.Write(r.Response(radius.CodeAccessReject))
	// 	return
	// }
	// if !passed {
	// 	w.Write(r.Response(radius.CodeAccessReject))
	// 	return
	// }
	// access, err := fe.CheckApplicationAccess(pi.appSlug)
	// if !access {
	// 	pi.log.WithField("username", username).Info("Access denied for user")
	// 	w.Write(r.Response(radius.CodeAccessReject))
	// 	return
	// }
	// if err != nil {
	// 	pi.log.WithField("username", username).WithError(err).Warning("failed to check access")
	// 	w.Write(r.Response(radius.CodeAccessReject))
	// 	return
	// }
	w.Write(r.Response(radius.CodeAccessAccept))
}
