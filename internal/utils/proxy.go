package utils

import (
	"net"

	"github.com/pires/go-proxyproto"
	log "github.com/sirupsen/logrus"
	"goauthentik.io/internal/config"
)

func GetProxyConnectionPolicy() proxyproto.ConnPolicyFunc {
	nets := []*net.IPNet{}
	for _, rn := range config.Get().Listen.TrustedProxyCIDRs {
		_, cidr, err := net.ParseCIDR(rn)
		if err != nil {
			continue
		}
		nets = append(nets, cidr)
	}
	return func(connPolicyOptions proxyproto.ConnPolicyOptions) (proxyproto.Policy, error) {
		host, _, err := net.SplitHostPort(connPolicyOptions.Upstream.String())
		if err == nil {
			// remoteAddr will be nil if the IP cannot be parsed
			remoteAddr := net.ParseIP(host)
			for _, allowedCidr := range nets {
				if remoteAddr != nil && allowedCidr.Contains(remoteAddr) {
					log.WithField("remoteAddr", remoteAddr).WithField("cidr", allowedCidr.String()).Trace("Using remote IP from proxy protocol")
					return proxyproto.USE, nil
				}
			}
		}
		return proxyproto.SKIP, nil
	}
}
