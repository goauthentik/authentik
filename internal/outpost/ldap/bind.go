package ldap

import (
	"net"
	"strings"

	"github.com/nmcclain/ldap"
)

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	bindDN = strings.ToLower(bindDN)
	ls.log.WithField("bindDN", bindDN).Info("bind")
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, bindDN, bindPW, conn)
		} else {
			ls.log.WithError(err).Debug("Username not for instance")
		}
	}
	ls.log.WithField("bindDN", bindDN).WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}
