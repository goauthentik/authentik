package ldap

import (
	"fmt"

	"github.com/nmcclain/ldap"
	"goauthentik.io/internal/constants"
)

func (pi *ProviderInstance) SearchBase(req SearchRequest, authz bool) (ldap.ServerSearchResult, error) {
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
						Values: []string{pi.BaseDN},
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
							pi.BaseDN,
							pi.GroupDN,
							pi.UserDN,
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
