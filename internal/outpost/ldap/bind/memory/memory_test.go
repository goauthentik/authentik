package memory

import (
	"net"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"beryju.io/ldap"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/flags"
	api "goauthentik.io/packages/client-go"
)

// fakeInstance is a minimal server.LDAPServerInstance stub. It only needs to make
// DirectBinder.Bind reach a real HTTP call to the (fake) authentik API - everything
// else is unused by the code paths under test.
type fakeInstance struct {
	apiClient *api.APIClient

	mu    sync.Mutex
	flags map[string]*flags.UserFlags
}

func newFakeInstance(apiURL string) *fakeInstance {
	cfg := api.NewConfiguration()
	cfg.Servers = api.ServerConfigurations{{URL: apiURL}}
	return &fakeInstance{
		apiClient: api.NewAPIClient(cfg),
		flags:     make(map[string]*flags.UserFlags),
	}
}

func (f *fakeInstance) GetAPIClient() *api.APIClient        { return f.apiClient }
func (f *fakeInstance) GetOutpostName() string              { return "test" }
func (f *fakeInstance) GetAuthenticationFlowSlug() string   { return "test-authentication-flow" }
func (f *fakeInstance) GetInvalidationFlowSlug() *string    { return nil }
func (f *fakeInstance) GetAppSlug() string                  { return "test" }
func (f *fakeInstance) GetProviderID() int32                { return 1 }
func (f *fakeInstance) UserEntry(u api.User) *ldap.Entry    { return nil }
func (f *fakeInstance) GetBaseDN() string                   { return "dc=test" }
func (f *fakeInstance) GetBaseGroupDN() string              { return "" }
func (f *fakeInstance) GetBaseVirtualGroupDN() string       { return "" }
func (f *fakeInstance) GetBaseUserDN() string               { return "" }
func (f *fakeInstance) GetMFASupport() bool                 { return false }
func (f *fakeInstance) GetUserDN(string) string             { return "" }
func (f *fakeInstance) GetGroupDN(string) string            { return "" }
func (f *fakeInstance) GetVirtualGroupDN(string) string     { return "" }
func (f *fakeInstance) GetUserUidNumber(api.User) string    { return "" }
func (f *fakeInstance) GetUserGidNumber(api.User) string    { return "" }
func (f *fakeInstance) GetGroupGidNumber(api.Group) string  { return "" }
func (f *fakeInstance) MembersForGroup(api.Group) []string  { return nil }
func (f *fakeInstance) MemberOfForGroup(api.Group) []string { return nil }
func (f *fakeInstance) GetNeededObjects(scope int, baseDN string, filterOC string) (bool, bool) {
	return false, false
}

func (f *fakeInstance) GetFlags(dn string) *flags.UserFlags {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.flags[dn]
}

func (f *fakeInstance) SetFlags(dn string, fl *flags.UserFlags) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.flags[dn] = fl
}

// fakeConn is a minimal net.Conn - only RemoteAddr is ever called by bind.NewRequest.
type fakeConn struct{}

func (fakeConn) Read(b []byte) (int, error)         { return 0, nil }
func (fakeConn) Write(b []byte) (int, error)        { return len(b), nil }
func (fakeConn) Close() error                       { return nil }
func (fakeConn) LocalAddr() net.Addr                { return &net.TCPAddr{} }
func (fakeConn) RemoteAddr() net.Addr               { return &net.TCPAddr{} }
func (fakeConn) SetDeadline(t time.Time) error      { return nil }
func (fakeConn) SetReadDeadline(t time.Time) error  { return nil }
func (fakeConn) SetWriteDeadline(t time.Time) error { return nil }

func newBindRequest(t *testing.T, dn, password string) *bind.Request {
	t.Helper()
	req, span := bind.NewRequest(ldap.BindRequest{BindDN: dn, Password: password}, fakeConn{})
	t.Cleanup(span.Finish)
	return req
}

// Regression test for the session-cache-poisoning bug: DirectBinder.Bind never
// returns a non-nil error for a rejected bind (it encodes every outcome, success or
// not, as an ldap.LDAPResultCode with a nil error). Before the fix, SessionBinder
// cached on `err == nil` alone, so a single transient failure (e.g. the flow API
// being unreachable) got cached and replayed as that same failure for the whole
// session TTL, even once the underlying cause was gone.
func TestSessionBinder_Bind_DoesNotCacheNonSuccess(t *testing.T) {
	var calls int32
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&calls, 1)
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer ts.Close()

	si := newFakeInstance(ts.URL)
	sb := NewSessionBinder(si, nil)

	dn := "cn=user,dc=test"
	password := "password"

	result, err := sb.Bind("user", newBindRequest(t, dn, password))
	require.NoError(t, err)
	assert.EqualValues(t, ldap.LDAPResultInvalidCredentials, result)
	assert.Equal(t, 0, sb.sessions.Len(), "a non-success bind result must not be cached")
	assert.Equal(t, int32(1), atomic.LoadInt32(&calls))

	// Retrying with the same (correct) credentials must execute the flow again,
	// not be served the stale rejection from the cache.
	result, err = sb.Bind("user", newBindRequest(t, dn, password))
	require.NoError(t, err)
	assert.EqualValues(t, ldap.LDAPResultInvalidCredentials, result)
	assert.Equal(t, 0, sb.sessions.Len())
	assert.Equal(t, int32(2), atomic.LoadInt32(&calls), "the flow must be re-executed instead of served from cache")
}

// A previously cached successful bind must still be served from the session cache
// without hitting the flow API again.
func TestSessionBinder_Bind_ServesCachedSuccessWithoutHittingFlow(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Errorf("unexpected request to flow API: %s", r.URL)
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer ts.Close()

	si := newFakeInstance(ts.URL)
	sb := NewSessionBinder(si, nil)

	dn := "cn=user,dc=test"
	password := "password"
	sb.sessions.Set(Credentials{DN: dn, Password: password}, ldap.LDAPResultSuccess, time.Minute)

	result, err := sb.Bind("user", newBindRequest(t, dn, password))
	require.NoError(t, err)
	assert.EqualValues(t, ldap.LDAPResultSuccess, result)
}
