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
						Name:   "supportedCapabilities",
						Values: []string{
							"1.2.840.113556.1.4.800", //LDAP_CAP_ACTIVE_DIRECTORY_OID
							"1.2.840.113556.1.4.1791", //LDAP_CAP_ACTIVE_DIRECTORY_LDAP_INTEG_OID
							"1.2.840.113556.1.4.1670", //LDAP_CAP_ACTIVE_DIRECTORY_V51_OID
							"1.2.840.113556.1.4.1880", //LDAP_CAP_ACTIVE_DIRECTORY_ADAM_DIGEST_OID
							"1.2.840.113556.1.4.1851", //LDAP_CAP_ACTIVE_DIRECTORY_ADAM_OID
							"1.2.840.113556.1.4.1920", //LDAP_CAP_ACTIVE_DIRECTORY_PARTIAL_SECRETS_OID
							"1.2.840.113556.1.4.1935", //LDAP_CAP_ACTIVE_DIRECTORY_V60_OID
							"1.2.840.113556.1.4.2080", //LDAP_CAP_ACTIVE_DIRECTORY_V61_R2_OID
							"1.2.840.113556.1.4.2237", //LDAP_CAP_ACTIVE_DIRECTORY_W8_OID
						},
					},
					{
						Name:   "supportedControl",
						Values: []string{
							"2.16.840.1.113730.3.4.9", //VLV Request LDAPv3 Control
							"2.16.840.1.113730.3.4.10", //VLV Response LDAPv3 Control
							"1.2.840.113556.1.4.474", //Sort result
							"1.2.840.113556.1.4.319", //Paged Result Control
						},
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
