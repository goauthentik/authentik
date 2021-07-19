package ldap

import (
	"errors"
	"net"
	"strings"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/google/uuid"
	"github.com/nmcclain/ldap"
	log "github.com/sirupsen/logrus"
)

type SearchRequest struct {
	ldap.SearchRequest
	BindDN string
	id     string
	conn   net.Conn
	log    *log.Entry
}

func (ls *LDAPServer) Search(bindDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	bindDN = strings.ToLower(bindDN)
	rid := uuid.New().String()
	req := SearchRequest{
		SearchRequest: searchReq,
		BindDN:        bindDN,
		conn:          conn,
		log:           ls.log.WithField("bindDN", bindDN).WithField("requestId", rid).WithField("client", conn.RemoteAddr().String()).WithField("filter", searchReq.Filter).WithField("baseDN", searchReq.BaseDN),
		id:            rid,
	}
	req.log.Info("Search request")

	if searchReq.BaseDN == "" {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultSuccess}, nil
	}
	bd, err := goldap.ParseDN(searchReq.BaseDN)
	if err != nil {
		req.log.WithError(err).Info("failed to parse basedn")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(provider.BaseDN)
		if providerBase.AncestorOf(bd) {
			return provider.Search(req)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("no provider could handle request")
}
