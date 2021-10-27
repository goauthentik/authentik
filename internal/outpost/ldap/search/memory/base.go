package memory

import (
	"fmt"

	"github.com/nmcclain/ldap"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ms *MemorySearcher) SearchBase(req *search.Request, authz bool) (ldap.ServerSearchResult, error) {
	dn := ""
	if authz {
		dn = req.SearchRequest.BaseDN
	}
	return ldap.ServerSearchResult{
		Entries: []*ldap.Entry{
			{
				DN: dn,
				Attributes: []*ldap.EntryAttribute{
					{
						Name:   "distinguishedName",
						Values: []string{ms.si.GetBaseDN()},
					},
					{
						Name:   "objectClass",
						Values: []string{"top", "domain"},
					},
					{
						Name:   "supportedLDAPVersion",
						Values: []string{"3"},
					},
					{
						Name: "namingContexts",
						Values: []string{
							ms.si.GetBaseDN(),
							ms.si.GetBaseUserDN(),
							ms.si.GetBaseGroupDN(),
						},
					},
					{
						Name:   "vendorName",
						Values: []string{"goauthentik.io"},
					},
					{
						Name:   "vendorVersion",
						Values: []string{fmt.Sprintf("authentik LDAP Outpost Version %s (build %s)", constants.VERSION, constants.BUILD())},
					},
				},
			},
		},
		Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess,
	}, nil
}
