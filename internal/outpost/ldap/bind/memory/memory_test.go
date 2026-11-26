package memory

import (
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"beryju.io/ldap"
	ttlcache "github.com/jellydator/ttlcache/v3"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"goauthentik.io/internal/outpost/ldap/bind"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/server"
	api "goauthentik.io/packages/client-go"
)

// fakeInstance carries the provider settings and minimal runtime hooks needed
// by the session binder and direct binder; any other method reached through
// the embedded nil interface panics, which is the point.
type fakeInstance struct {
	server.LDAPServerInstance
	bindFlow   string
	unbindFlow *string
	mfa        bool
	baseDN     string
	apiClient  *api.APIClient
	flagsMu    sync.RWMutex
	flags      map[string]*flags.UserFlags
}

func (f *fakeInstance) GetAuthenticationFlowSlug() string { return f.bindFlow }
func (f *fakeInstance) GetInvalidationFlowSlug() *string  { return f.unbindFlow }
func (f *fakeInstance) GetMFASupport() bool               { return f.mfa }
func (f *fakeInstance) GetBaseDN() string                 { return f.baseDN }
func (f *fakeInstance) GetAPIClient() *api.APIClient      { return f.apiClient }
func (f *fakeInstance) GetOutpostName() string            { return "test-outpost" }
func (f *fakeInstance) GetAppSlug() string                { return "test-ldap" }
func (f *fakeInstance) GetProviderID() int32              { return 1 }

func (f *fakeInstance) GetFlags(dn string) *flags.UserFlags {
	f.flagsMu.RLock()
	defer f.flagsMu.RUnlock()
	return f.flags[dn]
}

func (f *fakeInstance) SetFlags(dn string, fl *flags.UserFlags) {
	f.flagsMu.Lock()
	defer f.flagsMu.Unlock()
	if f.flags == nil {
		f.flags = make(map[string]*flags.UserFlags)
	}
	if fl == nil {
		delete(f.flags, dn)
	} else {
		f.flags[dn] = fl
	}
}

func newFakeInstance() *fakeInstance {
	unbind := "ldap-unbind"
	return &fakeInstance{
		bindFlow:   "ldap-bind",
		unbindFlow: &unbind,
		mfa:        false,
		baseDN:     "dc=ldap,dc=goauthentik,dc=io",
		flags:      make(map[string]*flags.UserFlags),
	}
}

func newFakeInstanceWithServer(t *testing.T, serverURL string) *fakeInstance {
	t.Helper()
	u, err := url.Parse(serverURL)
	require.NoError(t, err)
	cfg := api.NewConfiguration()
	cfg.Host = u.Host
	cfg.Scheme = u.Scheme
	cfg.Servers = api.ServerConfigurations{{URL: serverURL + "/api/v3"}}
	cfg.AddDefaultHeader("Authorization", "Bearer test-token")

	fi := newFakeInstance()
	fi.apiClient = api.NewAPIClient(cfg)
	return fi
}

type fakeConn struct{ net.Conn }

func (fakeConn) RemoteAddr() net.Addr {
	return &net.TCPAddr{IP: net.ParseIP("127.0.0.1"), Port: 12345}
}

func newBindRequest(t *testing.T, creds Credentials) *bind.Request {
	t.Helper()
	req, span := bind.NewRequest(ldap.BindRequest{
		BindDN:   creds.DN,
		Password: creds.Password,
	}, fakeConn{})
	t.Cleanup(span.Finish)
	return req
}

func writeJSON(w http.ResponseWriter, body string) {
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(body))
}

func successFlowHandler(t *testing.T, cookie *http.Cookie) http.HandlerFunc {
	t.Helper()
	user := api.NewUserSelf(
		1,
		"alice",
		"Alice",
		true,
		false,
		true,
		[]api.UserSelfGroups{},
		[]api.UserSelfRoles{},
		"",
		"alice-uid",
		map[string]any{},
		[]string{},
	)
	mePayload, err := json.Marshal(api.NewSessionUser(*user, []api.UserSelf{*user}))
	require.NoError(t, err)

	return func(w http.ResponseWriter, r *http.Request) {
		switch {
		case strings.Contains(r.URL.Path, "/flows/executor/"):
			if cookie != nil {
				http.SetCookie(w, cookie)
			}
			writeJSON(w, `{"component":"xak-flow-redirect","to":"/"}`)
		case strings.Contains(r.URL.Path, "/check_access/"):
			writeJSON(w, `{"access":{"passing":true,"messages":[],"log_messages":[]}}`)
		case strings.Contains(r.URL.Path, "/core/users/me/"):
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write(mePayload)
		default:
			w.WriteHeader(http.StatusNotFound)
		}
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

func TestSessionBinderSkipsCacheWhenSessionMissingOrNotPositiveTTL(t *testing.T) {
	cases := []struct {
		name         string
		priorFlags   *flags.UserFlags
		handler      http.HandlerFunc
		wantResult   ldap.LDAPResultCode
		wantCacheLen int
	}{
		{
			name: "missing session cookie does not panic or cache",
			handler: func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusServiceUnavailable)
			},
			wantResult:   ldap.LDAPResultInvalidCredentials,
			wantCacheLen: 0,
		},
		{
			name: "stale expired flags from prior bind are not cached forever on 503",
			priorFlags: &flags.UserFlags{
				Session: &http.Cookie{
					Name:    "authentik_session",
					Value:   "old-session",
					Expires: time.Now().Add(-10 * time.Minute),
				},
			},
			handler: func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusServiceUnavailable)
			},
			wantResult:   ldap.LDAPResultInvalidCredentials,
			wantCacheLen: 0,
		},
		{
			name: "cookie without Expires (session_duration=0) is not cached forever",
			handler: successFlowHandler(t, &http.Cookie{
				Name:  "authentik_session",
				Value: "browser-session",
			}),
			wantResult:   ldap.LDAPResultSuccess,
			wantCacheLen: 0,
		},
		{
			name: "already-expired cookie is not cached forever",
			handler: successFlowHandler(t, &http.Cookie{
				Name:    "authentik_session",
				Value:   "expired-session",
				Expires: time.Now().Add(-time.Minute),
			}),
			wantResult:   ldap.LDAPResultSuccess,
			wantCacheLen: 0,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			ts := httptest.NewServer(tc.handler)
			defer ts.Close()

			fi := newFakeInstanceWithServer(t, ts.URL)
			if tc.priorFlags != nil {
				fi.SetFlags(testCredentials.DN, tc.priorFlags)
			}
			sb := NewSessionBinder(fi, nil)
			t.Cleanup(sb.sessions.Stop)

			res, err := sb.Bind("alice", newBindRequest(t, testCredentials))
			require.NoError(t, err)
			assert.Equal(t, tc.wantResult, res)
			assert.Equal(t, tc.wantCacheLen, sb.sessions.Len())
			assert.Nil(t, sb.sessions.Get(testCredentials))
		})
	}
}

func TestSessionBinderCachesSessionWithPositiveExpiry(t *testing.T) {
	var flowCalls atomic.Int32
	cookie := &http.Cookie{
		Name:    "authentik_session",
		Value:   "valid-session",
		Expires: time.Now().Add(5 * time.Minute),
	}
	baseHandler := successFlowHandler(t, cookie)
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "/flows/executor/") {
			flowCalls.Add(1)
		}
		baseHandler(w, r)
	}))
	defer ts.Close()

	fi := newFakeInstanceWithServer(t, ts.URL)
	sb := NewSessionBinder(fi, nil)
	t.Cleanup(sb.sessions.Stop)

	res, err := sb.Bind("alice", newBindRequest(t, testCredentials))
	require.NoError(t, err)
	assert.Equal(t, ldap.LDAPResultCode(ldap.LDAPResultSuccess), res)
	assert.Equal(t, int32(1), flowCalls.Load())

	item := sb.sessions.Get(testCredentials)
	require.NotNil(t, item)
	assert.Positive(t, item.TTL())

	// Second bind with the same credentials is served from cache.
	res, err = sb.Bind("alice", newBindRequest(t, testCredentials))
	require.NoError(t, err)
	assert.Equal(t, ldap.LDAPResultCode(ldap.LDAPResultSuccess), res)
	assert.Equal(t, int32(1), flowCalls.Load())
}
