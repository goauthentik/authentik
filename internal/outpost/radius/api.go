package radius

import (
	"context"
	"errors"
	"net"
	"sort"
	"strings"

	"beryju.io/radius-eap/protocol"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ak"
)

func parseCIDRs(raw string) []*net.IPNet {
	parts := strings.Split(raw, ",")
	cidrs := make([]*net.IPNet, len(parts))
	for i, p := range parts {
		_, ipnet, err := net.ParseCIDR(strings.TrimSpace(p))
		if err != nil {
			log.WithError(err).WithField("cidr", p).Error("Failed to parse CIDR")
			continue
		}
		cidrs[i] = ipnet
	}
	sort.Slice(cidrs, func(i, j int) bool {
		_, bi := cidrs[i].Mask.Size()
		_, bj := cidrs[j].Mask.Size()
		return bi < bj
	})
	return cidrs
}

func (rs *RadiusServer) Refresh() error {
	apiProviders, err := ak.Paginator(rs.ac.Client.OutpostsAPI.OutpostsRadiusList(context.Background()), ak.PaginatorOptions{
		PageSize: 100,
		Logger:   rs.log,
	})
	if err != nil {
		return err
	}
	if len(apiProviders) < 1 {
		return errors.New("no radius provider defined")
	}
	providers := make(map[int32]*ProviderInstance)
	for _, provider := range apiProviders {
		existing, ok := rs.providers[provider.Pk]
		state := map[string]*protocol.State{}
		if ok {
			state = existing.eapState
		}
		logger := log.WithField("logger", "authentik.outpost.radius").WithField("provider", provider.Name)
		providers[provider.Pk] = &ProviderInstance{
			SharedSecret:   []byte(provider.GetSharedSecret()),
			ClientNetworks: parseCIDRs(provider.GetClientNetworks()),
			MFASupport:     provider.GetMfaSupport(),
			appSlug:        provider.ApplicationSlug,
			flowSlug:       provider.AuthFlowSlug,
			certId:         provider.GetCertificate(),
			providerId:     provider.Pk,
			s:              rs,
			log:            logger,
			eapState:       state,
		}
	}
	rs.providers = providers
	rs.log.Info("Update providers")
	return nil
}
