package constants

const OC = "objectClass"

const (
	OCTop         = "top"
	OCDomain      = "domain"
	OCNSContainer = "nsContainer"
	OCSubSchema   = "subschema"
)

const (
	SearchAttributeNone           = "1.1"
	SearchAttributeAllUser        = "*"
	SearchAttributeAllOperational = "+"
)

const (
	OCGroup              = "group"
	OCGroupOfUniqueNames = "groupOfUniqueNames"
	OCGroupOfNames       = "groupOfNames"
	OCAKGroup            = "goauthentik.io/ldap/group"
	OCAKVirtualGroup     = "goauthentik.io/ldap/virtual-group"
	OCPosixGroup         = "posixGroup"
)

const (
	OCUser          = "user"
	OCOrgPerson     = "organizationalPerson"
	OCInetOrgPerson = "inetOrgPerson"
	OCAKUser        = "goauthentik.io/ldap/user"
	OCPosixAccount  = "posixAccount"
)

const (
	OUUsers         = "users"
	OUGroups        = "groups"
	OUVirtualGroups = "virtual-groups"
)

func GetDomainOCs() map[string]bool {
	return map[string]bool{
		OCTop:    true,
		OCDomain: true,
	}
}

func GetContainerOCs() map[string]bool {
	return map[string]bool{
		OCTop:         true,
		OCNSContainer: true,
	}
}

func GetUserOCs() map[string]bool {
	return map[string]bool{
		OCUser:          true,
		OCOrgPerson:     true,
		OCInetOrgPerson: true,
		OCAKUser:        true,
		OCPosixAccount:  true,
	}
}

func GetGroupOCs() map[string]bool {
	return map[string]bool{
		OCGroup:              true,
		OCGroupOfUniqueNames: true,
		OCGroupOfNames:       true,
		OCAKGroup:            true,
		OCPosixGroup:         true,
	}
}

func GetVirtualGroupOCs() map[string]bool {
	return map[string]bool{
		OCGroup:              true,
		OCGroupOfUniqueNames: true,
		OCGroupOfNames:       true,
		OCAKVirtualGroup:     true,
	}
}
