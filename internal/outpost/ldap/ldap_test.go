package ldap_test

import (
	"testing"

	"beryju.io/ldap"
	"github.com/stretchr/testify/assert"
	oldap "goauthentik.io/internal/outpost/ldap"
)

func ProviderInstance() *oldap.ProviderInstance {
	return &oldap.ProviderInstance{
		BaseDN:         "dc=ldap,dc=goauthentik,dc=io",
		UserDN:         "ou=users,dc=ldap,dc=goauthentik,dc=io",
		VirtualGroupDN: "ou=virtual-groups,dc=ldap,dc=goauthentik,dc=io",
		GroupDN:        "ou=groups,dc=ldap,dc=goauthentik,dc=io",
	}
}

func AssertLDAPAttributes(t *testing.T, attrs []*ldap.EntryAttribute, expected *ldap.EntryAttribute) {
	found := false
	for _, attr := range attrs {
		if attr.Name == expected.Name {
			assert.Equal(t, expected.Values, attr.Values)
			found = true
		}
	}
	if !found {
		t.Fatalf("Key %s not found in ldap attributes", expected.Name)
	}
}
