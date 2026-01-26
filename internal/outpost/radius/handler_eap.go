package radius

import (
	"context"
	ttls "crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"errors"
	"net/url"

	eap "beryju.io/radius-eap"
	"beryju.io/radius-eap/protocol"
	"beryju.io/radius-eap/protocol/identity"
	"beryju.io/radius-eap/protocol/legacy_nak"
	"beryju.io/radius-eap/protocol/peap"
	"beryju.io/radius-eap/protocol/tls"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/flow"
	"goauthentik.io/internal/utils"
	"layeh.com/radius"
	"layeh.com/radius/rfc2869"
)

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
	settings := protocol.Settings{
		Logger: &logrusAdapter{pi.log},
		Protocols: []protocol.ProtocolConstructor{
			identity.Protocol,
			legacy_nak.Protocol,
		},
	}

	certId := pi.certId
	if certId == "" {
		return settings
	}

	cert := pi.s.cryptoStore.Get(certId)
	if cert == nil {
		return settings
	}

	settings.Protocols = append(settings.Protocols, tls.Protocol, peap.Protocol)
	settings.ProtocolPriority = []protocol.Type{
		identity.TypeIdentity,
		tls.TypeTLS,
	}
	settings.ProtocolSettings = map[protocol.Type]any{
		tls.TypeTLS: tls.Settings{
			Config: &ttls.Config{
				Certificates: []ttls.Certificate{*cert},
				ClientAuth:   ttls.RequireAnyClientCert,
			},
			HandshakeSuccessful: func(ctx protocol.Context, certs []*x509.Certificate) protocol.Status {
				ident := ctx.GetProtocolState(identity.TypeIdentity).(*identity.State).Identity

				ctx.Log().Debug("Starting authn flow")
				pem := pem.EncodeToMemory(&pem.Block{
					Type:  "CERTIFICATE",
					Bytes: certs[0].Raw,
				})

				fe := flow.NewFlowExecutor(context.Background(), pi.flowSlug, pi.s.ac.Client.GetConfig(), log.Fields{
					"client":   utils.GetIP(ctx.Packet().RemoteAddr),
					"identity": ident,
				})
				fe.Answers[flow.StageIdentification] = ident
				fe.DelegateClientIP(utils.GetIP(ctx.Packet().RemoteAddr))
				fe.Params.Add("goauthentik.io/outpost/radius", "true")
				fe.AddHeader("X-Authentik-Outpost-Certificate", url.QueryEscape(string(pem)))

				passed, err := fe.Execute()
				if err != nil {
					ctx.Log().Warn("failed to execute flow", "error", err)
					return protocol.StatusError
				}
				ctx.Log().Debug("Finished flow")
				if !passed {
					return protocol.StatusError
				}
				access, _, err := fe.ApiClient().OutpostsApi.OutpostsRadiusAccessCheck(context.Background(), pi.providerId).AppSlug(pi.appSlug).Execute()
				if err != nil {
					ctx.Log().Warn("failed to check access: %v", err)
					return protocol.StatusError
				}
				if !access.Access.Passing {
					ctx.Log().Info("Access denied for user")
					return protocol.StatusError
				}
				if access.HasAttributes() {
					ctx.AddResponseModifier(func(r, q *radius.Packet) error {
						rawData, err := base64.StdEncoding.DecodeString(access.GetAttributes())
						if err != nil {
							ctx.Log().Warn("failed to decode attributes from core: %v", err)
							return errors.New("attribute_decode_failed")
						}
						p, err := radius.Parse(rawData, pi.SharedSecret)
						if err != nil {
							ctx.Log().Warn("failed to parse attributes from core: %v", err)
							return errors.New("attribute_parse_failed")
						}
						for _, attr := range p.Attributes {
							r.Add(attr.Type, attr.Attribute)
						}
						return nil
					})
				}
				return protocol.StatusSuccess
			},
		},
	}
	return settings
}
