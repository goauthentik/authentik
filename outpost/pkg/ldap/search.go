package ldap

import (
	"errors"
	"net"

	goldap "github.com/go-ldap/ldap/v3"
	"github.com/nmcclain/ldap"
)

func (ls *LDAPServer) Search(boundDN string, searchReq ldap.SearchRequest, conn net.Conn) (ldap.ServerSearchResult, error) {
	ls.log.WithField("dn", boundDN).Info("search")
	bd, err := goldap.ParseDN(boundDN)
	if err != nil {
		return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
	}
	for _, provider := range ls.providers {
		providerBase, _ := goldap.ParseDN(provider.BaseDN)
		if providerBase.AncestorOf(bd) {
			return provider.Search(boundDN, searchReq, conn)
		}
	}
	return ldap.ServerSearchResult{ResultCode: ldap.LDAPResultOperationsError}, errors.New("invalid DN")
}
