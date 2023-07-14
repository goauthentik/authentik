package direct

import (
	"fmt"
	"strings"

	"beryju.io/ldap"
	"goauthentik.io/internal/constants"
	ldapConstants "goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ds *DirectSearcher) SearchBase(req *search.Request) (ldap.ServerSearchResult, error) {
	if req.Scope == ldap.ScopeSingleLevel {
		return ldap.ServerSearchResult{
			ResultCode: ldap.LDAPResultNoSuchObject,
		}, nil
	}
	return ldap.ServerSearchResult{
		Entries: []*ldap.Entry{
			{
				DN: "",
				Attributes: []*ldap.EntryAttribute{
					{
						Name:   "objectClass",
						Values: []string{ldapConstants.OCTop},
					},
					{
						Name:   "entryDN",
						Values: []string{""},
					},
					{
						Name:   "supportedLDAPVersion",
						Values: []string{"3"},
					},
					{
						Name:   "subschemaSubentry",
						Values: []string{"cn=subschema"},
					},
					{
						Name: "namingContexts",
						Values: []string{
							strings.ToLower(ds.si.GetBaseDN()),
						},
					},
					{
						Name: "rootDomainNamingContext",
						Values: []string{
							strings.ToLower(ds.si.GetBaseDN()),
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
