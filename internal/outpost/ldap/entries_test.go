package ldap_test

import (
	"testing"

	"beryju.io/ldap"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/api/v3"
)

func Test_UserEntry(t *testing.T) {
	pi := ProviderInstance()
	u := api.User{
		Username: "foo",
		Name:     "bar",
	}
	entry := pi.UserEntry(u)
	assert.Equal(t, "cn=foo,ou=users,dc=ldap,dc=goauthentik,dc=io", entry.DN)
	assert.Contains(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "cn",
		Values: []string{u.Username},
	})
	assert.Contains(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "displayName",
		Values: []string{u.Name},
	})
}
