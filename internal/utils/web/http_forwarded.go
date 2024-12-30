package web

import (
	"net"
	"net/http"

	"github.com/gorilla/handlers"
	"go.uber.org/zap"
	"goauthentik.io/internal/config"
)

// ProxyHeaders Set proxy headers like X-Forwarded-For and such, but only if the direct connection
// comes from a client that's in a list of trusted CIDRs
func ProxyHeaders() func(http.Handler) http.Handler {
	nets := []*net.IPNet{}
	for _, rn := range config.Get().Listen.TrustedProxyCIDRs {
		_, cidr, err := net.ParseCIDR(rn)
		if err != nil {
			continue
		}
		nets = append(nets, cidr)
	}
	ph := handlers.ProxyHeaders
	l := config.Get().Logger()
	return func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			host, _, err := net.SplitHostPort(r.RemoteAddr)
			if err == nil {
				// remoteAddr will be nil if the IP cannot be parsed
				remoteAddr := net.ParseIP(host)
				for _, allowedCidr := range nets {
					if remoteAddr != nil && allowedCidr.Contains(remoteAddr) {
						l.Debug("Setting proxy headers", config.Trace(), zap.String("remoteAddr", remoteAddr.String()), zap.String("cidr", allowedCidr.String()))
						ph(h).ServeHTTP(w, r)
						return
					}
				}
			}
			// Request is not directly coming from a CIDR we "trust"
			// so set XFF to the direct host IP
			r.Header.Set("X-Forwarded-For", host)
			h.ServeHTTP(w, r)
		})
	}
}
