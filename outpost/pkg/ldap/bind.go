package ldap

import (
	"net"

	"github.com/nmcclain/ldap"
)

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	ls.log.WithField("boundDN", bindDN).Info("bind")
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, bindPW, conn)
		}
	}
	ls.log.WithField("boundDN", bindDN).WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}
