package version

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

const (
	mainBranch = "main"
	mainTag    = "gh-main"
	releaseTag = "2026.8.0"
	serverRepo = "goauthentik/server"
)

func TestSafeBranchName(t *testing.T) {
	// Must match .github/actions/compute-container-tags, which substitutes
	// every character outside [a-zA-Z0-9-] with a dash.
	cases := map[string]string{
		mainBranch:             mainBranch,
		"version-2026.8":       "version-2026-8",
		"lifecycle/operator":   "lifecycle-operator",
		"refs/heads/main":      mainBranch,
		"feature/AK_123":       "feature-AK-123",
		"release/2026.8.0-rc1": "release-2026-8-0-rc1",
	}

	for branch, want := range cases {
		if got := SafeBranchName(branch); got != want {
			t.Errorf("SafeBranchName(%q) = %q, want %q", branch, got, want)
		}
	}
}

func TestBranchTag(t *testing.T) {
	if got, want := BranchTag("version-2026.8"), "gh-version-2026-8"; got != want {
		t.Errorf("BranchTag() = %q, want %q", got, want)
	}
}

func TestParseTag(t *testing.T) {
	pattern := buildTagPattern(mainBranch)

	result, ok := parseTag(pattern, "gh-main-1756600000-abc1234")
	if !ok {
		t.Fatal("expected gh-main-1756600000-abc1234 to parse")
	}
	if result.Commit != "abc1234" {
		t.Errorf("Commit = %q, want abc1234", result.Commit)
	}
	if want := time.Unix(1756600000, 0).UTC(); !result.BuildTime.Equal(want) {
		t.Errorf("BuildTime = %v, want %v", result.BuildTime, want)
	}

	rejected := []string{
		mainTag,                            // the moving tag carries no build info
		releaseTag,                         // a release tag
		"gh-other-1756600000-abc1234",      // a different branch
		"gh-main-1756600000-abc1234-extra", // trailing junk
		"gh-main-notatimestamp-abc1234",    // non-numeric timestamp
		"gh-main-1756600000-nothex",        // non-hex sha
		"gh-main-1756600000-abc12",         // sha too short
	}
	for _, tag := range rejected {
		if _, ok := parseTag(pattern, tag); ok {
			t.Errorf("expected %q to be rejected", tag)
		}
	}
}

func TestParseTagDoesNotConfuseBranchPrefixes(t *testing.T) {
	// A branch named "next" must not pick up builds of "next-gen".
	pattern := buildTagPattern("next")
	if _, ok := parseTag(pattern, "gh-next-gen-1756600000-abc1234"); ok {
		t.Error("branch \"next\" matched a gh-next-gen tag")
	}
	if _, ok := parseTag(pattern, "gh-next-1756600000-abc1234"); !ok {
		t.Error("branch \"next\" did not match its own tag")
	}
}

// tagServer is a minimal OCI distribution tag-listing endpoint.
func tagServer(t *testing.T, repo string, tags []string) *httptest.Server {
	t.Helper()

	mux := http.NewServeMux()
	mux.HandleFunc("/v2/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v2/" {
			w.WriteHeader(http.StatusOK)
			return
		}
		want := "/v2/" + repo + "/tags/list"
		if r.URL.Path != want {
			t.Errorf("unexpected path %q, want %q", r.URL.Path, want)
			w.WriteHeader(http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(map[string]any{"name": repo, "tags": tags}); err != nil {
			t.Errorf("failed to encode tag list: %v", err)
		}
	})

	server := httptest.NewServer(mux)
	t.Cleanup(server.Close)
	return server
}

func repositoryFor(t *testing.T, server *httptest.Server, repo string) string {
	t.Helper()
	parsed, err := url.Parse(server.URL)
	if err != nil {
		t.Fatalf("failed to parse server URL: %v", err)
	}
	return parsed.Host + "/" + repo
}

func TestResolveNewestPicksTheLatestBuild(t *testing.T) {
	repo := serverRepo
	server := tagServer(t, repo, []string{
		releaseTag,
		mainTag,
		"gh-main-1756600000-aaaaaaa",
		"gh-main-1756700000-ccccccc", // newest for main
		"gh-main-1756650000-bbbbbbb",
		"gh-version-2026-8-1756800000-ddddddd", // a different branch, newer
		"latest",
	})

	resolver := &RegistryResolver{PlainHTTP: true}
	result, err := resolver.ResolveNewest(context.Background(), Request{
		Repository: repositoryFor(t, server, repo),
		Branch:     mainBranch,
	})
	if err != nil {
		t.Fatalf("ResolveNewest: %v", err)
	}

	if want := "gh-main-1756700000-ccccccc"; result.Tag != want {
		t.Errorf("Tag = %q, want %q", result.Tag, want)
	}
	if result.Commit != "ccccccc" {
		t.Errorf("Commit = %q, want ccccccc", result.Commit)
	}
}

func TestResolveNewestErrorsWhenTheBranchHasNoBuilds(t *testing.T) {
	repo := serverRepo
	server := tagServer(t, repo, []string{releaseTag, "gh-main", "latest"})

	resolver := &RegistryResolver{PlainHTTP: true}
	_, err := resolver.ResolveNewest(context.Background(), Request{
		Repository: repositoryFor(t, server, repo),
		Branch:     mainBranch,
	})
	if err == nil {
		t.Fatal("expected an error when no per-build tag exists")
	}
	if !strings.Contains(err.Error(), ErrNoMatchingTag.Error()) {
		t.Errorf("error = %v, want it to wrap ErrNoMatchingTag", err)
	}
}

func TestResolveNewestRejectsUnqualifiedRepositories(t *testing.T) {
	resolver := NewRegistryResolver()
	_, err := resolver.ResolveNewest(context.Background(), Request{
		Repository: "server",
		Branch:     mainBranch,
	})
	if err == nil {
		t.Fatal("expected an error for a repository with no registry host")
	}
}

func TestResolveNewestRequiresABranch(t *testing.T) {
	resolver := NewRegistryResolver()
	if _, err := resolver.ResolveNewest(context.Background(), Request{
		Repository: "ghcr.io/goauthentik/server",
	}); err == nil {
		t.Fatal("expected an error when no branch is given")
	}
}
