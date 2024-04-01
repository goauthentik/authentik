package radius

import (
	"context"
	"errors"
	"net"
	"sort"
	"strings"
	"sync"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ldap/flags"
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

func (rs *RadiusServer) getCurrentProvider(pk int32) *ProviderInstance {
	for _, p := range rs.providers {
		if p.providerPk == pk {
			return p
		}
	}
	return nil
}

func (rs *RadiusServer) getInvalidationFlow() string {
	req, _, err := rs.ac.Client.CoreApi.CoreBrandsCurrentRetrieve(context.Background()).Execute()
	if err != nil {
		rs.log.WithError(err).Warning("failed to fetch brand config")
		return ""
	}
	flow := req.GetFlowInvalidation()
	return flow
}

func (rs *RadiusServer) Refresh() error {
	outposts, _, err := rs.ac.Client.OutpostsApi.OutpostsRadiusList(context.Background()).Execute()
	if err != nil {
		return err
	}
	if len(outposts.Results) < 1 {
		return errors.New("no radius provider defined")
	}
	invalidationFlow := rs.getInvalidationFlow()
	providers := make([]*ProviderInstance, len(outposts.Results))
	for idx, provider := range outposts.Results {
		logger := log.WithField("logger", "authentik.outpost.radius").WithField("provider", provider.Name)

		// Get existing instance so we can transfer boundUsers
		existing := rs.getCurrentProvider(provider.Pk)
		usersMutex := &sync.RWMutex{}
		users := make(map[string]*flags.UserFlags)
		if existing != nil {
			usersMutex = existing.boundUsersMutex
			// Shallow copy, no need to lock
			users = existing.boundUsers
		}

		providers[idx] = &ProviderInstance{
			SharedSecret:           []byte(provider.GetSharedSecret()),
			ClientNetworks:         parseCIDRs(provider.GetClientNetworks()),
			MFASupport:             provider.GetMfaSupport(),
			appSlug:                provider.ApplicationSlug,
			authenticationFlowSlug: provider.AuthFlowSlug,
			invalidationFlowSlug:   invalidationFlow,
			s:                      rs,
			log:                    logger,
			providerPk:             provider.Pk,
			boundUsersMutex:        usersMutex,
			boundUsers:             users,
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
