package memory

import (
	"testing"

	"beryju.io/ldap"
	ttlcache "github.com/jellydator/ttlcache/v3"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/ldap/server"
)

// fakeInstance carries only the provider settings the session binder and
// the direct binder's GetUsername read; any other method reached through
// the embedded nil interface panics, which is the point.
type fakeInstance struct {
	server.LDAPServerInstance
	bindFlow   string
	unbindFlow *string
	mfa        bool
	baseDN     string
}

func (f *fakeInstance) GetAuthenticationFlowSlug() string { return f.bindFlow }
func (f *fakeInstance) GetInvalidationFlowSlug() *string  { return f.unbindFlow }
func (f *fakeInstance) GetMFASupport() bool               { return f.mfa }
func (f *fakeInstance) GetBaseDN() string                 { return f.baseDN }

func newFakeInstance() *fakeInstance {
	unbind := "ldap-unbind"
	return &fakeInstance{
		bindFlow:   "ldap-bind",
		unbindFlow: &unbind,
		mfa:        false,
		baseDN:     "dc=ldap,dc=goauthentik,dc=io",
	}
}

var testCredentials = Credentials{
	DN:       "cn=alice,ou=users,dc=ldap,dc=goauthentik,dc=io",
	Password: "correct horse battery staple",
}

func TestNewSessionBinderKeepsSessionsWhenBindSettingsAreUnchanged(t *testing.T) {
	old := NewSessionBinder(newFakeInstance(), nil)
	old.sessions.Set(testCredentials, ldap.LDAPResultSuccess, ttlcache.NoTTL)

	sb := NewSessionBinder(newFakeInstance(), old)

	assert.NotNil(t, sb.sessions.Get(testCredentials), "a refresh with the same bind settings keeps the cached sessions")
}

func TestNewSessionBinderDropsSessionsWhenBindSettingsChange(t *testing.T) {
	otherUnbind := "ldap-unbind-strict"
	cases := map[string]func(*fakeInstance){
		"bind flow":   func(f *fakeInstance) { f.bindFlow = "ldap-bind-strict" },
		"unbind flow": func(f *fakeInstance) { f.unbindFlow = &otherUnbind },
		"no unbind":   func(f *fakeInstance) { f.unbindFlow = nil },
		"mfa support": func(f *fakeInstance) { f.mfa = true },
		"base dn":     func(f *fakeInstance) { f.baseDN = "dc=example,dc=org" },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			old := NewSessionBinder(newFakeInstance(), nil)
			// A refusal is cached like a success, and must go the same way.
			old.sessions.Set(testCredentials, ldap.LDAPResultInvalidCredentials, ttlcache.NoTTL)

			changed := newFakeInstance()
			change(changed)
			sb := NewSessionBinder(changed, old)

			assert.Nil(t, sb.sessions.Get(testCredentials), "a changed %s discards the cached sessions", name)
		})
	}
}

func TestNewSessionBinderRebuildsDirectBinderFromTheNewInstance(t *testing.T) {
	old := NewSessionBinder(newFakeInstance(), nil)

	moved := newFakeInstance()
	moved.baseDN = "dc=example,dc=org"
	sb := NewSessionBinder(moved, old)

	// GetUsername checks the DN against the direct binder's own instance,
	// so this only passes if that binder was built from the new one.
	username, err := sb.GetUsername("cn=alice,ou=users,dc=example,dc=org")
	assert.NoError(t, err)
	assert.Equal(t, "alice", username)
}
