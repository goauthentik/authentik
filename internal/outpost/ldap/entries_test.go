package ldap_test

import (
	"testing"
	"time"

	"beryju.io/ldap"
	"github.com/stretchr/testify/assert"
	api "goauthentik.io/packages/client-go"
)

func Test_UserEntry(t *testing.T) {
	pi := ProviderInstance()
	dateJoined := time.Date(2025, 1, 2, 3, 4, 5, 0, time.UTC)
	passwordChanged := time.Date(2026, 2, 3, 4, 5, 6, 0, time.UTC)
	u := api.User{
		Username:   "foo",
		Name:       "bar",
		DateJoined: dateJoined,
	}
	u.PasswordDevice.Set(&api.PasswordDevice{PasswordChangeDate: passwordChanged})
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
	assert.Contains(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "pwdChangedTime",
		Values: []string{"20260203040506Z"},
	})

	u.PasswordDevice.Set(nil)
	entry = pi.UserEntry(u)
	assert.Contains(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "pwdChangedTime",
		Values: []string{"20250102030405Z"},
	})
}
