package radius

import (
	"context"
	"errors"
	"net"
	"sort"
	"strings"

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
	apiProviders, err := ak.Paginator(rs.ac.Client.OutpostsApi.OutpostsRadiusList(context.Background()), ak.PaginatorOptions{
		PageSize: 100,
		Logger:   rs.log,
	})
	if err != nil {
		return err
	}
	if len(apiProviders) < 1 {
		return errors.New("no radius provider defined")
	}
	providers := make([]*ProviderInstance, len(apiProviders))
	for idx, provider := range apiProviders {
		logger := log.WithField("logger", "authentik.outpost.radius").WithField("provider", provider.Name)
		providers[idx] = &ProviderInstance{
			SharedSecret:   []byte(provider.GetSharedSecret()),
			ClientNetworks: parseCIDRs(provider.GetClientNetworks()),
			MFASupport:     provider.GetMfaSupport(),
			appSlug:        provider.ApplicationSlug,
			flowSlug:       provider.AuthFlowSlug,
			providerId:     provider.Pk,
			s:              rs,
			log:            logger,
		}
	}
	rs.providers = providers
	rs.log.Info("Update providers")
	return nil
}

func (rs *RadiusServer) StartRadiusServer() error {
	rs.log.WithField("listen", rs.s.Addr).Info("Starting radius server")
	return rs.s.ListenAndServe()
}
