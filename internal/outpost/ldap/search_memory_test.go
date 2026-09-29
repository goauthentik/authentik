package ldap

import (
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sync"
	"testing"
	"time"

	"beryju.io/ldap"
	log "github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"goauthentik.io/internal/outpost/ak"
	"goauthentik.io/internal/outpost/ldap/flags"
	"goauthentik.io/internal/outpost/ldap/search"
	"goauthentik.io/internal/outpost/ldap/search/memory"
	api "goauthentik.io/packages/client-go"
)

const (
	memTestBaseDN  = "dc=ldap,dc=goauthentik,dc=io"
	memTestUserDN  = "ou=users,dc=ldap,dc=goauthentik,dc=io"
	memTestGroupDN = "ou=groups,dc=ldap,dc=goauthentik,dc=io"
	memTestVGDN    = "ou=virtual-groups,dc=ldap,dc=goauthentik,dc=io"

	memTestAliceDN  = "cn=alice,ou=users,dc=ldap,dc=goauthentik,dc=io"
	memTestGroupXPk = "00000000-0000-0000-0000-0000000000a0"
	memTestGroupYPk = "00000000-0000-0000-0000-0000000000b0"
)

// memDirectory is the mutable fixture set the fake authentik API serves.
type memDirectory struct {
	mu     sync.Mutex
	users  []api.User
	groups []api.Group
}

func (d *memDirectory) set(users []api.User, groups []api.Group) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.users = users
	d.groups = groups
}

func (d *memDirectory) snapshot() ([]api.User, []api.Group) {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.users, d.groups
}

// memNoMorePages is a pagination block with next=0, so ak.Paginator stops
// after the first page.
func memNoMorePages(count int) api.Pagination {
	return api.Pagination{
		Next:       0,
		Previous:   0,
		Count:      float32(count),
		Current:    1,
		TotalPages: 1,
		StartIndex: 1,
		EndIndex:   float32(count),
	}
}

func memAliceUser(groups []api.PartialGroup) api.User {
	ts := time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)
	isActive := true
	email := "alice@goauthentik.io"
	groupPks := make([]string, len(groups))
	for i, g := range groups {
		groupPks[i] = g.Pk
	}
	return api.User{
		Pk:                 1,
		Username:           "alice",
		Name:               "Alice",
		IsActive:           &isActive,
		DateJoined:         ts,
		IsSuperuser:        false,
		Groups:             groupPks,
		GroupsObj:          groups,
		RolesObj:           []api.Role{},
		Email:              &email,
		Avatar:             "",
		Uid:                "alice-uid",
		Uuid:               "00000000-0000-0000-0000-00000000a11c",
		PasswordChangeDate: ts,
		LastUpdated:        ts,
	}
}

func memAlicePartial() api.PartialUser {
	isActive := true
	return api.PartialUser{
		Pk:       1,
		Username: "alice",
		Name:     "Alice",
		IsActive: &isActive,
		Uid:      "alice-uid",
	}
}

func memPartialGroup(pk string, numPk int32, name string) api.PartialGroup {
	isSuperuser := false
	return api.PartialGroup{
		Pk:          pk,
		NumPk:       numPk,
		Name:        name,
		IsSuperuser: &isSuperuser,
	}
}

func memGroup(pk string, numPk int32, name string, users []api.PartialUser) api.Group {
	isSuperuser := false
	userPks := make([]int32, len(users))
	for i, u := range users {
		userPks[i] = u.Pk
	}
	return api.Group{
		Pk:                pk,
		NumPk:             numPk,
		Name:              name,
		IsSuperuser:       &isSuperuser,
		ParentsObj:        []api.RelatedGroup{},
		Users:             userPks,
		UsersObj:          users,
		RolesObj:          []api.Role{},
		InheritedRolesObj: []api.Role{},
		Children:          []string{},
		ChildrenObj:       []api.RelatedGroup{},
	}
}

func memNewAPIClient(t *testing.T, dir *memDirectory) (*api.APIClient, func()) {
	t.Helper()
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v3/core/users/", func(w http.ResponseWriter, r *http.Request) {
		users, _ := dir.snapshot()
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(api.PaginatedUserList{
			Pagination:   memNoMorePages(len(users)),
			Results:      users,
			Autocomplete: map[string]interface{}{},
		}); err != nil {
			t.Errorf("failed to encode users: %v", err)
		}
	})
	mux.HandleFunc("/api/v3/core/groups/", func(w http.ResponseWriter, r *http.Request) {
		_, groups := dir.snapshot()
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(api.PaginatedGroupList{
			Pagination:   memNoMorePages(len(groups)),
			Results:      groups,
			Autocomplete: map[string]interface{}{},
		}); err != nil {
			t.Errorf("failed to encode groups: %v", err)
		}
	})
	srv := httptest.NewServer(mux)

	akURL, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatalf("failed to parse test server url: %v", err)
	}
	cfg := api.NewConfiguration()
	cfg.Host = akURL.Host
	cfg.Scheme = akURL.Scheme
	cfg.HTTPClient = srv.Client()
	cfg.Servers = api.ServerConfigurations{{URL: "api/v3"}}
	return api.NewAPIClient(cfg), srv.Close
}

func memProviderInstance(client *api.APIClient) *ProviderInstance {
	return &ProviderInstance{
		BaseDN:          memTestBaseDN,
		UserDN:          memTestUserDN,
		GroupDN:         memTestGroupDN,
		VirtualGroupDN:  memTestVGDN,
		s:               &LDAPServer{ac: &ak.APIController{Client: client}},
		log:             log.WithField("logger", "authentik.outpost.ldap.test"),
		boundUsersMutex: &sync.RWMutex{},
		boundUsers:      map[string]*flags.UserFlags{},
		uidStartNumber:  2000,
		gidStartNumber:  4000,
	}
}

func memSelfSearch(t *testing.T, searcher *memory.MemorySearcher) *ldap.Entry {
	t.Helper()
	client, server := net.Pipe()
	defer func() {
		_ = client.Close()
		_ = server.Close()
	}()
	req, span := search.NewRequest(memTestAliceDN, ldap.SearchRequest{
		BaseDN: memTestAliceDN,
		Scope:  ldap.ScopeBaseObject,
		Filter: "(objectClass=person)",
	}, client)
	defer span.Finish()
	if req.FilterObjectClass != "person" {
		t.Fatalf("expected filter object class person, got %q", req.FilterObjectClass)
	}
	res, err := searcher.Search(req)
	if err != nil {
		t.Fatalf("search failed: %v", err)
	}
	if len(res.Entries) != 1 {
		t.Fatalf("expected exactly 1 entry, got %d", len(res.Entries))
	}
	return res.Entries[0]
}

func memAssertAttribute(t *testing.T, attrs []*ldap.EntryAttribute, expected *ldap.EntryAttribute) {
	t.Helper()
	for _, attr := range attrs {
		if attr.Name == expected.Name {
			assert.Equal(t, expected.Values, attr.Values)
			return
		}
	}
	t.Fatalf("Key %s not found in ldap attributes", expected.Name)
}

// TestMemorySearcherRefreshesUserEntry pins that a non-searching user's own
// entry follows the cache across a refresh, rather than being frozen at the
// value it had on their first search.
func TestMemorySearcherRefreshesUserEntry(t *testing.T) {
	groupX := memPartialGroup(memTestGroupXPk, 10, "x")
	groupY := memPartialGroup(memTestGroupYPk, 11, "y")

	dir := &memDirectory{}
	dir.set(
		[]api.User{memAliceUser([]api.PartialGroup{groupX})},
		[]api.Group{
			memGroup(memTestGroupXPk, 10, "x", []api.PartialUser{memAlicePartial()}),
			memGroup(memTestGroupYPk, 11, "y", []api.PartialUser{}),
		},
	)

	client, closeServer := memNewAPIClient(t, dir)
	defer closeServer()

	pi := memProviderInstance(client)
	pi.SetFlags(memTestAliceDN, &flags.UserFlags{UserPk: 1, CanSearch: false})

	searcher := memory.NewMemorySearcher(pi, nil)

	entry := memSelfSearch(t, searcher)
	assert.Equal(t, memTestAliceDN, entry.DN)
	memAssertAttribute(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "memberOf",
		Values: []string{pi.GetGroupDN("x")},
	})

	// Alice moves from group x to group y.
	dir.set(
		[]api.User{memAliceUser([]api.PartialGroup{groupY})},
		[]api.Group{
			memGroup(memTestGroupXPk, 10, "x", []api.PartialUser{}),
			memGroup(memTestGroupYPk, 11, "y", []api.PartialUser{memAlicePartial()}),
		},
	)

	// This is the path Refresh() takes: it re-initialises through the public
	// constructor, which re-runs fetch() on the existing searcher.
	searcher = memory.NewMemorySearcher(pi, searcher)

	entry = memSelfSearch(t, searcher)
	assert.Equal(t, memTestAliceDN, entry.DN)
	memAssertAttribute(t, entry.Attributes, &ldap.EntryAttribute{
		Name:   "memberOf",
		Values: []string{pi.GetGroupDN("y")},
	})

	// White-box: the leak was a pointer into the cached user slice stored on
	// the per-DN flags, which pinned an entire stale copy for the process
	// lifetime. The memory searcher must never populate it.
	assert.Nil(t, pi.GetFlags(memTestAliceDN).UserInfo)
}
