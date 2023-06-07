package direct

import (
	"fmt"

	"beryju.io/ldap"
	"goauthentik.io/internal/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ds *DirectSearcher) SearchBase(req *search.Request, authz bool) (ldap.ServerSearchResult, error) {
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
						Values: []string{ds.si.GetBaseDN()},
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
							ds.si.GetBaseDN(),
							ds.si.GetBaseUserDN(),
							ds.si.GetBaseGroupDN(),
						},
					},
					{
						Name:   "vendorName",
						Values: []string{"goauthentik.io"},
					},
					{
						Name:   "vendorVersion",
						Values: []string{fmt.Sprintf("authentik LDAP Outpost Version %s", constants.FullVersion())},
					},
				},
			},
		},
		Referrals: []string{}, Controls: []ldap.Control{}, ResultCode: ldap.LDAPResultSuccess,
	}, nil
}
