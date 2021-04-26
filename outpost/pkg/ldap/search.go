package ldap

import (
	"errors"
	"net"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
)

func (ls *LDAPServer) Search(boundDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	ls.log.WithField("boundDN", boundDN).WithField("baseDN", searchReq.BaseDN).Info("search")
	if searchReq.BaseDN == "" {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultSuccess}, nil
	}
	bd, err := goldap.ParseDN(searchReq.BaseDN)
	if err != nil {
		ls.log.WithField("baseDN", searchReq.BaseDN).WithError(err).Info("failed to parse basedn")
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(provider.BaseDN)
		if providerBase.AncestorOf(bd) {
			return provider.Search(boundDN, searchReq, conn)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("no provider could handle request")
}
