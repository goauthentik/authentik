package ldap

import (
	"net"
	"strings"

	"github.com/google/uuid"
	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
)

type BindRequest struct {
	BindDN string
	BindPW string
	id     string
	conn   net.Conn
	log    *log.Entry
}

func (ls *LDAPServer) Bind(bindDN string, bindPW string, conn net.Conn) (ldap.LDAPResultCode, error) {
	bindDN = strings.ToLower(bindDN)
	rid := uuid.New().String()
	req := BindRequest{
		BindDN: bindDN,
		BindPW: bindPW,
		conn:   conn,
		log:    ls.log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", conn.RemoteAddr().String()),
		id:     rid,
	}
	req.log.Info("Bind request")
	for _, instance := range ls.providers {
		username, err := instance.getUsername(bindDN)
		if err == nil {
			return instance.Bind(username, req)
		} else {
			ls.log.WithError(err).Debug("Username not for instance")
		}
	}
	req.log.WithField("request", "bind").Warning("No provider found for request")
	return ldap.LDAPResultOperationsError, nil
}
