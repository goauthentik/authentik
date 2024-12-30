package utils

import (
	"net"

	"github.com/pires/go-proxyproto"
	"go.uber.org/zap"
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
					log.Debug("Using remote IP from proxy protocol", config.Trace(), zap.String("remoteAddr", remoteAddr.String()), zap.String("cidr", allowedCidr.String()))
					return proxyproto.USE, nil
				}
			}
		}
		return proxyproto.SKIP, nil
	}
}
