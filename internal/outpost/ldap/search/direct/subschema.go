package direct

import (
	"github.com/nmcclain/ldap"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ds *DirectSearcher) SearchSubschema(req *search.Request) (ldap.ServerSearchResult, error) {
	return ldap.ServerSearchResult{
		Entries: []*ldap.Entry{
			{
				DN: req.BaseDN,
				Attributes: []*ldap.EntryAttribute{
					{
						Name:   "cn",
						Values: []string{"schema"},
					},
					{
						Name:   constants.OC,
						Values: []string{constants.OCTop, "subSchema"},
					},
					{
						Name: "ldapSyntaxes",
						Values: []string{
							"( 1.3.6.1.4.1.1466.115.121.1.40 DESC 'Octet String' )",
						},
					},
					{
						Name: "objectClasses",
						Values: []string{
							"( 2.5.6.0 NAME 'top' DESC 'top of the superclass chain' ABSTRACT MUST objectClass )",
						},
					},
					{
						Name: "attributeTypes",
						Values: []string{
							"( 2.5.4.0 NAME 'objectClass' DESC 'RFC4512: object classes of the entity' EQUALITY objectIdentifierMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.38 )",
							"( 1.3.6.1.1.4 NAME 'vendorName' DESC 'RFC3045: name of implementation vendor' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.40 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							"( 1.3.6.1.1.5 NAME 'vendorVersion' DESC 'RFC3045: version of implementation' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.40 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
						},
					},
				},
			},
		},
	}, nil
}
