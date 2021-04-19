package ldap

import (
	"net"

	"github.com/nmcclain/ldap"
)

func (ls *LDAPServer) Bind(bindDN string, bindSimplePw string, conn net.Conn) (ldap.LDAPResultCode, error) {
	ls.log.WithField("dn", bindDN).WithField("pw", bindSimplePw).Debug("bind")
	return ldap.LDAPResultSuccess, nil
}
