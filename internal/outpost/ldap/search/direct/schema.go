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
							"( 1.3.6.1.4.1.1466.115.121.1.7 DESC 'Boolean' )",
						},
					},
					{
						Name: "objectClasses",
						Values: []string{
							"( 2.5.6.0 NAME 'top' DESC 'top of the superclass chain' ABSTRACT MUST objectClass )",
							"( 2.5.6.9 NAME 'groupOfNames' DESC 'RFC2256: a group of names (DNs)' SUP top STRUCTURAL MUST ( member $cn ) MAY ( businessCategory $ seeAlso $ owner $ ou $ o $ description ) )",
							"( 2.5.6.17 NAME 'groupOfUniqueNames' DESC 'RFC2256: a group of unique names (DN and Unique Identifier)' SUP top STRUCTURAL MUST ( uniqueMember $ cn ) MAY ( businessCategory $ seeAlso $ owner $ ou $ o $ description ) )",
							"( 1.3.6.1.1.1.2.2 NAME 'posixGroup' DESC 'Abstraction of a group of accounts' SUP top STRUCTURAL MUST ( cn $ gidNumber ) MAY ( userPassword $ memberUid $ description ) )",
							"( 2.5.6.7 NAME 'organizationalPerson' DESC 'RFC2256: an organizational person' SUP person STRUCTURAL MAY ( title $ x121Address $ registeredAddress $ destinationIndicator $ preferredDeliveryMethod $ telexNumber $ teletexTerminalIdentifier $ telephoneNumber $ internationaliSDNNumber $ facsimileTelephoneNumber $ street $ postOfficeBox $ postalCode $ postalAddress $ physicalDeliveryOfficeName $ ou $ st $ l ) )",
							"( 2.16.840.1.113730.3.2.2 NAME 'inetOrgPerson' DESC 'RFC2798: Internet Organizational Person' SUP organizationalPerson STRUCTURAL MAY ( audio $ businessCategory $ carLicense $ departmentNumber $ displayName $ employeeNumber $ employeeType $ givenName $ homePhone $ homePostalAddress $ initials $ jpegPhoto $ labeledURI $ mail $ manager $ mobile $ o $ pager $ photo $ roomNumber $ secretary $ uid $ userCertificate $ x500uniqueIdentifier $ preferredLanguage $ userSMIMECertificate $ userPKCS12 ) )",
							"( 1.3.6.1.1.1.2.0 NAME 'posixAccount' DESC 'Abstraction of an a ccount with POSIX attributes' SUP top AUXILIARY MUST ( cn $ uid $ uidNumber $gidNumber $ homeDirectory ) MAY ( userPassword $ loginShell $ gecos $ description ) )",
						},
					},
					{
						Name: "attributeTypes",
						Values: []string{
							"( 2.5.4.0 NAME 'objectClass' DESC 'RFC4512: object classes of the entity' EQUALITY objectIdentifierMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.38 )",
							"( 1.3.6.1.1.4 NAME 'vendorName' DESC 'RFC3045: name of implementation vendor' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.40 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							"( 1.3.6.1.1.5 NAME 'vendorVersion' DESC 'RFC3045: version of implementation' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.40 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							// Custom attributes
							// Temporarily use 1.3.6.1.4.1.26027.1.1 as a base
							// https://docs.oracle.com/cd/E19450-01/820-6169/working-with-object-identifiers.html#obtaining-a-base-oid
							"( 1.3.6.1.4.1.26027.1.1.1 NAME 'ak-superuser' DESC 'Superuser status of a user' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.7 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
							"( 1.3.6.1.4.1.26027.1.1.2 NAME 'ak-active' DESC 'Active status of a user' EQUALITY caseExactMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.7 SINGLE-VALUE NO-USER-MODIFICATION USAGE dSAOperation )",
						},
					},
				},
			},
		},
	}, nil
}
