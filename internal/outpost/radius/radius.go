package radius

import (
	"context"
	"crypto/tls"
	"net"
	"sort"

	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/crypto"
	"goauthentik.io/internal/outpost/ak"

	"layeh.com/radius"
)

type ProviderInstance struct {
	ClientNetworks []*net.IPNet
	SharedSecret   []byte

	appSlug  string
	flowSlug string
	s        *RadiusServer
	log      *log.Entry

	// tlsServerName *string
	cert *tls.Certificate
}

type RadiusServer struct {
	s           radius.PacketServer
	log         *log.Entry
	ac          *ak.APIController
	defaultCert *tls.Certificate

	providers []*ProviderInstance
}

func NewServer(ac *ak.APIController) *RadiusServer {
	rs := &RadiusServer{
		log:       log.WithField("logger", "authentik.outpost.radius"),
		ac:        ac,
		providers: []*ProviderInstance{},
	}

	server := radius.PacketServer{
		Handler:      rs,
		SecretSource: rs,
	}

	defaultCert, err := crypto.GenerateSelfSignedCert()
	if err != nil {
		log.Warning(err)
	}
	rs.defaultCert = &defaultCert
	rs.s = server
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
