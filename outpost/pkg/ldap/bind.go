package ldap

import (
	"net"

	"github.com/nmcclain/ldap"
)

type UIDResponse struct {
	UIDFIeld string `json:"uid_field"`
}

type PasswordResponse struct {
	Password string `json:"password"`
}

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, bindPW, conn)
		}
	}
	ls.log.WithField("dn", bindDN).WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}
