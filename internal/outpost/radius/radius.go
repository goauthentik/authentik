package radius

import (
	"context"
	"net"
	"sort"
	"sync"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/radius/metrics"

	"layeh.com/radius"
)

type ProviderInstance struct {
	ClientNetworks []*net.IPNet
	SharedSecret   []byte
	MFASupport     bool

	appSlug  string
	flowSlug string
	s        *RadiusServer
	log      *log.Entry
}

type RadiusServer struct {
	s   radius.PacketServer
	log *log.Entry
	ac  *ak.APIController

	providers []*ProviderInstance
}

func NewServer(ac *ak.APIController) *RadiusServer {
	rs := &RadiusServer{
		log:       log.WithField("logger", "authentik.outpost.radius"),
		ac:        ac,
		providers: []*ProviderInstance{},
	}
	rs.s = radius.PacketServer{
		Handler:      rs,
		SecretSource: rs,
		Addr:         config.Get().Listen.Radius,
	}
	return rs
}

type cpp struct {
	c *net.IPNet
	p *ProviderInstance
}

func (rs *RadiusServer) RADIUSSecret(ctx context.Context, remoteAddr net.Addr) ([]byte, error) {
	matchedPrefixes := []cpp{}

	host, _, err := net.SplitHostPort(remoteAddr.String())
	if err != nil {
		rs.log.WithError(err).Warning("Failed to get remote IP")
		return nil, err
	}
	ip := net.ParseIP(host)

	// Check all networks we have and remember all matching prefixes
	for _, p := range rs.providers {
		for _, cidr := range p.ClientNetworks {
			if cidr.Contains(ip) {
				matchedPrefixes = append(matchedPrefixes, cpp{
					c: cidr,
					p: p,
				})
			}
		}
	}
	if len(matchedPrefixes) < 1 {
		rs.log.WithField("ip", ip.String()).Warning("No matching prefixes found")
		return []byte{}, nil
	}
	// Sort matched cidrs by prefix length
	sort.Slice(matchedPrefixes, func(i, j int) bool {
		_, bi := matchedPrefixes[i].c.Mask.Size()
		_, bj := matchedPrefixes[j].c.Mask.Size()
		return bi < bj
	})
	candidate := matchedPrefixes[0]
	rs.log.WithField("ip", ip.String()).WithField("cidr", candidate.c.String()).Debug("Matched CIDR")
	return candidate.p.SharedSecret, nil
}

func (rs *RadiusServer) Start() error {
	wg := sync.WaitGroup{}
	wg.Add(2)
	go func() {
		defer wg.Done()
		metrics.RunServer()
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

func (rs *RadiusServer) Stop() error {
	ctx, cancel := context.WithCancel(context.Background())
	err := rs.s.Shutdown(ctx)
	cancel()
	return err
}

func (rs *RadiusServer) TimerFlowCacheExpiry(context.Context) {}

func (rs *RadiusServer) Type() string {
	return "radius"
}
