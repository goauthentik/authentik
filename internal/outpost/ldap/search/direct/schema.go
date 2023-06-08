package direct

import (
	"beryju.io/ldap"
	"goauthentik.io/internal/outpost/ldap/constants"
	"goauthentik.io/internal/outpost/ldap/search"
)

func (ds *DirectSearcher) SearchSubschema(req *search.Request) (ldap.ServerSearchResult, error) {
	return ldap.ServerSearchResult{
		Entries: []*ldap.Entry{
			{
				DN: "cn=subschema",
				Attributes: []*ldap.EntryAttribute{
					{
						Name:   "cn",
						Values: []string{"subschema"},
					},
					{
						Name:   constants.OC,
						Values: []string{constants.OCTop, "subSchema"},
					},
					{
						Name: "ldapSyntaxes",
						Values: []string{
							"( 1.3.6.1.4.1.1466.115.121.1.40 DESC 'Octet String' )",
							"( 1.3.6.1.4.1.1466.115.121.1.15 DESC 'Directory String' )",
							"( 1.3.6.1.4.1.1466.115.121.1.7 DESC 'Boolean' )",
						},
					},
					{
						Name: "objectClasses",
						Values: []string{
							"( 2.5.6.0 NAME 'top' ABSTRACT MUST ( objectClass ) MAY (cn $ description $ displayName $ memberOf $ name ) )",
							"( 2.5.6.6 NAME 'person' SUP top STRUCTURAL MUST ( cn ) MAY (sn $ telephoneNumber ) )",
							"( 2.5.6.7 NAME 'organizationalPerson' SUP person STRUCTURAL MAY (c $ l $ o $ ou $ title $ givenName $ co $ department $ company $ division $ mail $ mobile $ telephoneNumber ) )",
							"( 2.5.6.9 NAME 'groupOfNames' SUP top STRUCTURAL MUST (cn $ member ) MAY (o $ ou ) )",
							"( 1.2.840.113556.1.5.9 NAME 'user' SUP organizationalPerson STRUCTURAL MAY ( name $ displayName $ uid $ mail ) )",
							"( 1.3.6.1.1.1.2.0 NAME 'posixAccount' SUP top AUXILIARY MAY (cn $ description $ homeDirectory $ uid $ uidNumber $ gidNumber ) )",
							"( 2.16.840.1.113730.3.2.2 NAME 'inetOrgPerson' AUX ( posixAccount ) MUST ( sAMAccountName ) MAY ( uidNumber $ gidNumber ))",
							// Custom attributes
							// Temporarily use 1.3.6.1.4.1.26027.1.1 as a base
							// https://docs.oracle.com/cd/E19450-01/820-6169/working-with-object-identifiers.html#obtaining-a-base-oid
							"( 1.3.6.1.4.1.26027.1.1.1 NAME 'goauthentik.io/ldap/user' SUP organizationalPerson STRUCTURAL MAY ( ak-active $ sAMAccountName $ goauthentikio-user-sources $ goauthentik.io/user/sources $ goauthentik.io/ldap/active $ goauthentik.io/ldap/superuser $ goauthentikio-user-override-ips $ goauthentikio-user-service-account ) )",
						},
					},
					{
						Name: "attributeTypes",
						Values: []string{
							"( 2.5.4.0 NAME 'objectClass' DESC 'RFC4512: object classes of the entity' EQUALITY objectIdentifierMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.38 )",
							"( 1.3.6.1.4.1.1466.101.120.5 NAME 'namingContexts' DESC 'RFC4512: naming contexts' SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 USAGE dSAOperation )",
							"( 2.5.18.10 NAME 'subschemaSubentry' DESC 'RFC4512: name of controlling subschema entry' EQUALITY distinguishedNameMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 SINGLE-VALUE NO-USER-MODIFICATION USAGE directoryOperation )",
							"( 1.3.6.1.4.1.1466.101.120.15 NAME 'supportedLDAPVersion' DESC 'RFC4512: supported LDAP versions' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 USAGE dSAOperation )",
							"( 1.3.6.1.1.20 NAME 'entryDN' DESC 'DN of the entry' EQUALITY distinguishedNameMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 SINGLE-VALUE NO-USER-MODIFICATION USAGE directoryOperation )",
							"( 1.3.6.1.1.4 NAME 'vendorName' DESC 'RFC3045: name of implementation vendor' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							"( 1.3.6.1.1.5 NAME 'vendorVersion' DESC 'RFC3045: version of implementation' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							"( 0.9.2342.19200300.100.1.1 NAME 'uid' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 0.9.2342.19200300.100.1.3 NAME 'mail' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 0.9.2342.19200300.100.1.41 NAME 'mobile' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.2.102 NAME 'memberOf' SYNTAX '1.3.6.1.4.1.1466.115.121.1.12' NO-USER-MODIFICATION )",
							"( 1.2.840.113556.1.2.13 NAME 'displayName' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.4.1 NAME 'name' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE NO-USER-MODIFICATION )",
							"( 1.2.840.113556.1.2.131 NAME 'co' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.2.141 NAME 'department' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.2.146 NAME 'company' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.4.44 NAME 'homeDirectory' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.4.221 NAME 'sAMAccountName' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.2.840.113556.1.4.261 NAME 'division' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 1.3.6.1.1.1.1.0 NAME 'uidNumber' SYNTAX '1.3.6.1.4.1.1466.115.121.1.27' SINGLE-VALUE )",
							"( 1.3.6.1.1.1.1.1 NAME 'gidNumber' SYNTAX '1.3.6.1.4.1.1466.115.121.1.27' SINGLE-VALUE )",
							"( 2.5.4.6 NAME 'c' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.7 NAME 'l' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.10 NAME 'o' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' )",
							"( 2.5.4.11 NAME 'ou' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' )",
							"( 2.5.4.20 NAME 'telephoneNumber' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.42 NAME 'givenName' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.0 NAME 'objectClass' SYNTAX '1.3.6.1.4.1.1466.115.121.1.38' NO-USER-MODIFICATION )",
							"( 2.5.4.3 NAME 'cn' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.4 NAME 'sn' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.12 NAME 'title' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' SINGLE-VALUE )",
							"( 2.5.4.13 NAME 'description' SYNTAX '1.3.6.1.4.1.1466.115.121.1.15' )",
							"( 2.5.4.31 NAME 'member' SYNTAX '1.3.6.1.4.1.1466.115.121.1.12' )",
							// Custom attributes
							// Temporarily use 1.3.6.1.4.1.26027.1.1 as a base
							// https://docs.oracle.com/cd/E19450-01/820-6169/working-with-object-identifiers.html#obtaining-a-base-oid
							"( 1.3.6.1.4.1.26027.1.1.2 NAME ( 'goauthentik.io/ldap/superuser' 'ak-superuser' ) SYNTAX '1.3.6.1.4.1.1466.115.121.1.7' SINGLE-VALUE )",
							"( 1.3.6.1.4.1.26027.1.1.3 NAME ( 'goauthentik.io/ldap/active' 'ak-active' ) SYNTAX '1.3.6.1.4.1.1466.115.121.1.7' SINGLE-VALUE )",
							"( 1.3.6.1.4.1.26027.1.1.4 NAME 'goauthentikio-user-override-ips' SYNTAX '1.3.6.1.4.1.1466.115.121.1.7' SINGLE-VALUE )",
							"( 1.3.6.1.4.1.26027.1.1.5 NAME 'goauthentikio-user-service-account' SYNTAX '1.3.6.1.4.1.1466.115.121.1.7 SINGLE-VALUE' )",
						},
					},
				},
			},
		},
	}, nil
}
