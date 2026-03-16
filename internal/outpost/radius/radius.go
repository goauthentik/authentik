package radius

import (
	"context"
	"net"
	"sort"
	"sync"

	"beryju.io/radius-eap/protocol"
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

	appSlug    string
	flowSlug   string
	providerId int32
	certId     string
	s          *RadiusServer
	log        *log.Entry
	eapState   map[string]*protocol.State
}

type RadiusServer struct {
	s           []*radius.PacketServer
	log         *log.Entry
	ac          *ak.APIController
	cryptoStore *ak.CryptoStore

	providers map[int32]*ProviderInstance
}

func NewServer(ac *ak.APIController) ak.Outpost {
	rs := &RadiusServer{
		log:         log.WithField("logger", "authentik.outpost.radius"),
		ac:          ac,
		providers:   map[int32]*ProviderInstance{},
		cryptoStore: ak.NewCryptoStore(ac.Client.CryptoAPI),
	}
	listenRadius := config.Get().Listen.Radius
	for _, listen := range listenRadius {
		rs.s = append(rs.s, &radius.PacketServer{
			Handler:      rs,
			SecretSource: rs,
			Addr:         listen,
		})
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
	rs.log.WithField("ip", ip.String()).WithField("cidr", candidate.c.String()).WithField("instance", candidate.p.appSlug).Debug("Matched CIDR")
	return candidate.p.SharedSecret, nil
}

func (rs *RadiusServer) Start() error {
	listenMetrics := config.Get().Listen.Metrics
	wg := sync.WaitGroup{}
	wg.Add(len(rs.s) + len(listenMetrics))
	for _, s := range rs.s {
		go func() {
			defer wg.Done()
			rs.log.WithField("listen", s.Addr).Info("Starting radius server")
			err := s.ListenAndServe()
			if err != nil {
				panic(err)
			}
		}()
	}
	for _, listen := range listenMetrics {
		go func() {
			defer wg.Done()
			metrics.RunServer(listen)
		}()
	}
	wg.Wait()
	return nil
}

func (rs *RadiusServer) Stop() error {
	ctx, cancel := context.WithCancel(context.Background())
	var err []error
	for _, s := range rs.s {
		err = append(err, s.Shutdown(ctx))
	}
	cancel()
	for _, err := range err {
		if err != nil {
			return err
		}
	}
	return nil
}

func (rs *RadiusServer) TimerFlowCacheExpiry(context.Context) {}

func (rs *RadiusServer) Type() string {
	return "radius"
}
