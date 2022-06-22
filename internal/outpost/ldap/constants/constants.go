package constants

const (
	OCTop         = "top"
	OCDomain      = "domain"
	OCNSContainer = "nsContainer"
)

const (
	OCGroup              = "group"
	OCGroupOfUniqueNames = "groupOfUniqueNames"
	OCGroupOfNames       = "groupOfNames"
	OCAKGroup            = "goauthentik.io/ldap/group"
	OCAKVirtualGroup     = "goauthentik.io/ldap/virtual-group"
)

const (
	OCUser          = "user"
	OCOrgPerson     = "organizationalPerson"
	OCInetOrgPerson = "inetOrgPerson"
	OCAKUser        = "goauthentik.io/ldap/user"
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
	}
}

func GetGroupOCs() map[string]bool {
	return map[string]bool{
		OCGroup:              true,
		OCGroupOfUniqueNames: true,
		OCGroupOfNames:       true,
		OCAKGroup:            true,
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
