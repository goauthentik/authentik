package radius

import (
	"context"
	ttls "crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"net/url"

	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/outpost/radius/eap"
	"goauthentik.io/internal/outpost/radius/eap/protocol"
	"goauthentik.io/internal/outpost/radius/eap/protocol/identity"
	"goauthentik.io/internal/outpost/radius/eap/protocol/legacy_nak"
	"goauthentik.io/internal/outpost/radius/eap/protocol/peap"
	"goauthentik.io/internal/outpost/radius/eap/protocol/tls"
	"goauthentik.io/internal/outpost/radius/metrics"
	"goauthentik.io/internal/utils"
	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
	"layeh.com/radius/rfc2869"
)

func (rs *RadiusServer) Handle_AccessRequest(w radius.ResponseWriter, r *RadiusRequest) {
	eap := rfc2869.EAPMessage_Get(r.Packet)
	if len(eap) > 0 {
		rs.log.Trace("EAP request")
		rs.Handle_AccessRequest_EAP(w, r)
	} else {
		rs.log.Trace("PAP request")
		rs.Handle_AccessRequest_PAP(w, r)
	}
}

func (rs *RadiusServer) Handle_AccessRequest_PAP(w radius.ResponseWriter, r *RadiusRequest) {
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

func (rs *RadiusServer) Handle_AccessRequest_EAP(w radius.ResponseWriter, r *RadiusRequest) {
	er := rfc2869.EAPMessage_Get(r.Packet)
	ep, err := eap.Decode(r.pi, er)
	if err != nil {
		rs.log.WithError(err).Warning("failed to parse EAP packet")
		return
	}
	ep.HandleRadiusPacket(w, r.Request)
}

func (pi *ProviderInstance) GetEAPState(key string) *protocol.State {
	return pi.eapState[key]
}

func (pi *ProviderInstance) SetEAPState(key string, state *protocol.State) {
	pi.eapState[key] = state
}

func (pi *ProviderInstance) GetEAPSettings() protocol.Settings {
	protocols := []protocol.ProtocolConstructor{
		identity.Protocol,
		legacy_nak.Protocol,
	}

	certId := pi.certId
	if certId == "" {
		return protocol.Settings{
			Protocols: protocols,
		}
	}

	cert := pi.s.cryptoStore.Get(certId)
	if cert == nil {
		return protocol.Settings{
			Protocols: protocols,
		}
	}

	return protocol.Settings{
		Protocols: append(protocols, tls.Protocol, peap.Protocol),
		ProtocolPriority: []protocol.Type{
			tls.TypeTLS,
			peap.TypePEAP,
		},
		ProtocolSettings: map[protocol.Type]interface{}{
			tls.TypeTLS: tls.Settings{
				Config: &ttls.Config{
					Certificates: []ttls.Certificate{*cert},
					ClientAuth:   ttls.RequireAnyClientCert,
				},
				HandshakeSuccessful: func(ctx protocol.Context, certs []*x509.Certificate) protocol.Status {
					ctx.Log().Debug("Starting authn flow")
					pem := pem.EncodeToMemory(&pem.Block{
						Type:  "CERTIFICATE",
						Bytes: certs[0].Raw,
					})

					fe := flow.NewFlowExecutor(context.Background(), pi.flowSlug, pi.s.ac.Client.GetConfig(), log.Fields{
						"client": utils.GetIP(ctx.Packet().RemoteAddr),
					})
					fe.DelegateClientIP(utils.GetIP(ctx.Packet().RemoteAddr))
					fe.Params.Add("goauthentik.io/outpost/radius", "true")
					fe.AddHeader("X-Authentik-Outpost-Certificate", url.QueryEscape(string(pem)))

					passed, err := fe.Execute()
					if err != nil {
						ctx.Log().WithError(err).Warning("failed to execute flow")
						return protocol.StatusError
					}
					ctx.Log().WithField("passed", passed).Debug("Finished flow")
					if passed {
						return protocol.StatusSuccess
					} else {
						return protocol.StatusError
					}
				},
			},
			peap.TypePEAP: peap.Settings{
				Config: &ttls.Config{
					Certificates: []ttls.Certificate{*cert},
				},
				InnerProtocols: protocol.Settings{},
			},
		},
	}
}
