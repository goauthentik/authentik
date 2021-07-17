package radius

import (
	"context"
	"errors"
	"net"
	"net/http"
	"sort"
	"strings"
	"sync"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/outpost/ak"
)

func parseCIDRs(raw string) []*net.IPNet {
	parts := strings.Split(raw, ",")
	cidrs := make([]*net.IPNet, 0, len(parts))
	for i, p := range parts {
		_, ipnet, err := net.ParseCIDR(p)
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
	outposts, _, err := rs.ac.Client.OutpostsApi.OutpostsRadiusList(context.Background()).Execute()
	if err != nil {
		return err
	}
	if len(outposts.Results) < 1 {
		return errors.New("no radius provider defined")
	}
	providers := make([]*ProviderInstance, len(outposts.Results))
	for idx, provider := range outposts.Results {
		logger := log.WithField("logger", "authentik.outpost.radius").WithField("provider", provider.Name)
		s := *provider.SharedSecret
		c := *provider.ClientNetworks
		providers[idx] = &ProviderInstance{
			SharedSecret:   []byte(s),
			ClientNetworks: parseCIDRs(c),
			appSlug:        provider.ApplicationSlug,
			flowSlug:       provider.AuthFlowSlug,
			s:              rs,
			log:            logger,
		}
		if provider.Certificate.Get() != nil {
			logger.WithField("provider", provider.Name).Debug("Enabling TLS")
			cert, err := ak.ParseCertificate(*provider.Certificate.Get(), rs.ac.Client.CryptoApi)
			if err != nil {
				logger.WithField("provider", provider.Name).WithError(err).Warning("Failed to fetch certificate")
			} else {
				providers[idx].cert = cert
				logger.WithField("provider", provider.Name).Debug("Loaded certificates")
			}
		}
	}
	rs.providers = providers
	rs.log.Info("Update providers")
	return nil
}

func (rs *RadiusServer) StartHTTPServer() error {
	listen := "0.0.0.0:4180" // same port as proxy
	m := http.NewServeMux()
	m.HandleFunc("/akprox/ping", func(rw http.ResponseWriter, r *http.Request) {
		rw.WriteHeader(204)
	})
	rs.log.WithField("listen", listen).Info("Starting http server")
	return http.ListenAndServe(listen, m)
}

func (rs *RadiusServer) StartRadiusServer() error {
	listen := "0.0.0.0:1812"
	rs.log.WithField("listen", listen).Info("Starting radius server")
	return rs.s.ListenAndServe()
}

func (rs *RadiusServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		err := rs.StartHTTPServer()
		if err != nil {
			panic(err)
		}
	}()
	go func() {
		defer wg.Done()
		err := rs.StartRadiusServer()
		if err != nil {
			panic(err)
		}
	}()
	wg.Wait()
	return nil
}
