package ldap

import (
	"context"
	"net"

	"github.com/goauthentik/ldap"
)

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn, ctx context.Context) (ldap.LDAPResultCode, error) {
	ls.log.WithField("boundDN", bindDN).Info("bind")
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, bindPW, conn, ctx)
		}
	}
	ls.log.WithField("boundDN", bindDN).WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}
