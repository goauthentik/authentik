package ldap

import (
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
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
	mu         sync.Mutex
	users      []api.User
	groups     []api.Group
	failUsers  bool
	failGroups bool
}

func (d *memDirectory) set(users []api.User, groups []api.Group) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.users = users
	d.groups = groups
}

// setFailing makes the fake API answer the users and/or groups list with a
// server error.
func (d *memDirectory) setFailing(users, groups bool) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.failUsers = users
	d.failGroups = groups
}

func (d *memDirectory) failing() (bool, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.failUsers, d.failGroups
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

func memNewAPIClient(t testing.TB, dir *memDirectory) (*api.APIClient, func()) {
	t.Helper()
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v3/core/users/", func(w http.ResponseWriter, r *http.Request) {
		if failUsers, _ := dir.failing(); failUsers {
			http.Error(w, "unavailable", http.StatusServiceUnavailable)
			return
		}
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
		if _, failGroups := dir.failing(); failGroups {
			http.Error(w, "unavailable", http.StatusServiceUnavailable)
			return
		}
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

// TestMemorySearcherKeepsSnapshotOnFetchError pins that a refresh which fails
// to fetch users or groups keeps serving the previous snapshot, instead of
// replacing a known-good directory with an empty or partial one.
func TestMemorySearcherKeepsSnapshotOnFetchError(t *testing.T) {
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
	memAssertAttribute(t, memSelfSearch(t, searcher).Attributes, &ldap.EntryAttribute{
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

	for _, tc := range []struct {
		name                  string
		failUsers, failGroups bool
	}{
		{"users", true, false},
		// The users fetch succeeds here, but must not be applied on its own.
		{"groups", false, true},
		{"both", true, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir.setFailing(tc.failUsers, tc.failGroups)
			searcher = memory.NewMemorySearcher(pi, searcher)
			memAssertAttribute(t, memSelfSearch(t, searcher).Attributes, &ldap.EntryAttribute{
				Name:   "memberOf",
				Values: []string{pi.GetGroupDN("x")},
			})
		})
	}

	// Once the API recovers, the next refresh applies the new data.
	dir.setFailing(false, false)
	searcher = memory.NewMemorySearcher(pi, searcher)
	memAssertAttribute(t, memSelfSearch(t, searcher).Attributes, &ldap.EntryAttribute{
		Name:   "memberOf",
		Values: []string{pi.GetGroupDN("y")},
	})
}

// TestMemorySearcherFirstFetchError pins that when the very first fetch fails
// partially, the searcher serves what it did get, and a later successful
// refresh replaces it.
func TestMemorySearcherFirstFetchError(t *testing.T) {
	groupX := memPartialGroup(memTestGroupXPk, 10, "x")

	dir := &memDirectory{}
	dir.set(
		[]api.User{memAliceUser([]api.PartialGroup{groupX})},
		[]api.Group{
			memGroup(memTestGroupXPk, 10, "x", []api.PartialUser{memAlicePartial()}),
		},
	)
	dir.setFailing(false, true)

	client, closeServer := memNewAPIClient(t, dir)
	defer closeServer()

	pi := memProviderInstance(client)
	pi.SetFlags(memTestAliceDN, &flags.UserFlags{UserPk: 1, CanSearch: false})

	searcher := memory.NewMemorySearcher(pi, nil)
	assert.Equal(t, memTestAliceDN, memSelfSearch(t, searcher).DN)

	dir.setFailing(false, false)
	searcher = memory.NewMemorySearcher(pi, searcher)
	memAssertAttribute(t, memSelfSearch(t, searcher).Attributes, &ldap.EntryAttribute{
		Name:   "memberOf",
		Values: []string{pi.GetGroupDN("x")},
	})
}

// memUser is a plain user with no groups, for directories of more than one.
func memUser(pk int32, username string) api.User {
	ts := time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)
	isActive := true
	email := username + "@goauthentik.io"
	return api.User{
		Pk:                 pk,
		Username:           username,
		Name:               username,
		IsActive:           &isActive,
		DateJoined:         ts,
		IsSuperuser:        false,
		Groups:             []string{},
		GroupsObj:          []api.PartialGroup{},
		RolesObj:           []api.Role{},
		Email:              &email,
		Avatar:             "",
		Uid:                username + "-uid",
		Uuid:               "00000000-0000-0000-0000-000000000000",
		PasswordChangeDate: ts,
		LastUpdated:        ts,
	}
}

// memSearchAs runs one base-object search as the given bind DN and returns
// the entries, so a test can look up an entry other than the binder's own.
func memSearchAs(tb testing.TB, searcher *memory.MemorySearcher, bindDN, baseDN, filter string) []*ldap.Entry {
	tb.Helper()
	client, server := net.Pipe()
	defer func() {
		_ = client.Close()
		_ = server.Close()
	}()
	req, span := search.NewRequest(bindDN, ldap.SearchRequest{
		BaseDN: baseDN,
		Scope:  ldap.ScopeBaseObject,
		Filter: filter,
	}, client)
	defer span.Finish()
	res, err := searcher.Search(req)
	if err != nil {
		tb.Fatalf("search failed: %v", err)
	}
	return res.Entries
}

// memSearchDirectory is alice, bob and carol, with bob in group x and an
// empty group y.
func memSearchDirectory() ([]api.User, []api.Group) {
	groupX := memPartialGroup(memTestGroupXPk, 10, "x")
	bob := memUser(2, "bob")
	bob.Groups = []string{groupX.Pk}
	bob.GroupsObj = []api.PartialGroup{groupX}
	bobPartial := api.PartialUser{Pk: 2, Username: "bob", Name: "bob", IsActive: bob.IsActive, Uid: bob.Uid}
	return []api.User{memAliceUser([]api.PartialGroup{}), bob, memUser(3, "carol")},
		[]api.Group{
			memGroup(memTestGroupXPk, 10, "x", []api.PartialUser{bobPartial}),
			memGroup(memTestGroupYPk, 11, "y", []api.PartialUser{}),
		}
}

// TestMemorySearcherSearchPermissionLooksUpOneUserByDN pins that a binder with
// search permission asking for one user by DN gets exactly that user's entry,
// whatever the DN's case, and nothing for a DN that is not in the directory.
// The searcher used to build an entry for every cached user on such a request
// and keep the one whose DN matched, which on a large directory was the whole
// cost of every lookup.
func TestMemorySearcherSearchPermissionLooksUpOneUserByDN(t *testing.T) {
	dir := &memDirectory{}
	dir.set(memSearchDirectory())

	client, closeServer := memNewAPIClient(t, dir)
	defer closeServer()

	pi := memProviderInstance(client)
	pi.SetFlags(memTestAliceDN, &flags.UserFlags{UserPk: 1, CanSearch: true})

	searcher := memory.NewMemorySearcher(pi, nil)

	bobDN := pi.GetUserDN("bob")

	entries := memSearchAs(t, searcher, memTestAliceDN, bobDN, "(objectClass=*)")
	if assert.Len(t, entries, 1) {
		assert.Equal(t, bobDN, entries[0].DN)
		memAssertAttribute(t, entries[0].Attributes, &ldap.EntryAttribute{
			Name:   "memberOf",
			Values: []string{pi.GetGroupDN("x")},
		})
	}

	entries = memSearchAs(t, searcher, memTestAliceDN, "CN=Bob,"+memTestUserDN, "(objectClass=*)")
	if assert.Len(t, entries, 1) {
		assert.Equal(t, bobDN, entries[0].DN)
	}

	assert.Empty(t, memSearchAs(t, searcher, memTestAliceDN, pi.GetUserDN("nobody"), "(objectClass=*)"))

	// A binder without search permission still only ever sees their own entry.
	pi.SetFlags(memTestAliceDN, &flags.UserFlags{UserPk: 1, CanSearch: false})
	assert.Empty(t, memSearchAs(t, searcher, memTestAliceDN, bobDN, "(objectClass=*)"))
	assert.Equal(t, memTestAliceDN, memSelfSearch(t, searcher).DN)
}

// TestMemorySearcherSearchPermissionLooksUpOneGroupByDN pins the same for a
// group asked for by DN: one entry, with its members, and nothing for an
// unknown group.
func TestMemorySearcherSearchPermissionLooksUpOneGroupByDN(t *testing.T) {
	dir := &memDirectory{}
	dir.set(memSearchDirectory())

	client, closeServer := memNewAPIClient(t, dir)
	defer closeServer()

	pi := memProviderInstance(client)
	pi.SetFlags(memTestAliceDN, &flags.UserFlags{UserPk: 1, CanSearch: true})

	searcher := memory.NewMemorySearcher(pi, nil)

	groupXDN := pi.GetGroupDN("x")

	entries := memSearchAs(t, searcher, memTestAliceDN, groupXDN, "(objectClass=group)")
	if assert.Len(t, entries, 1) {
		assert.Equal(t, groupXDN, entries[0].DN)
		memAssertAttribute(t, entries[0].Attributes, &ldap.EntryAttribute{
			Name:   "member",
			Values: []string{pi.GetUserDN("bob")},
		})
	}

	assert.Empty(t, memSearchAs(t, searcher, memTestAliceDN, pi.GetGroupDN("nothing"), "(objectClass=group)"))
}

// BenchmarkMemorySearcherSearchPermissionUserLookup measures one base-object
// lookup of one user by a binder with search permission against a directory
// of five thousand users: the shape a TAK server's per-connection poll takes.
func BenchmarkMemorySearcherSearchPermissionUserLookup(b *testing.B) {
	users := make([]api.User, 0, 5000)
	for i := int32(1); i <= 5000; i++ {
		users = append(users, memUser(i, "user"+strconv.Itoa(int(i))))
	}
	dir := &memDirectory{}
	dir.set(users, []api.Group{})

	client, closeServer := memNewAPIClient(b, dir)
	defer closeServer()

	pi := memProviderInstance(client)
	binderDN := pi.GetUserDN("user1")
	pi.SetFlags(binderDN, &flags.UserFlags{UserPk: 1, CanSearch: true})

	searcher := memory.NewMemorySearcher(pi, nil)
	targetDN := pi.GetUserDN("user2500")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if entries := memSearchAs(b, searcher, binderDN, targetDN, "(objectClass=*)"); len(entries) != 1 {
			b.Fatalf("expected 1 entry, got %d", len(entries))
		}
	}
}
