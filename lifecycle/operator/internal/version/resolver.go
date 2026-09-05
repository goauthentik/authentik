// Package version resolves a git branch to the container image tag holding that
// branch's newest build.
//
// authentik's CI publishes two tags per build (see
// .github/actions/compute-container-tags):
//
//   - gh-<branch>, a moving tag that always points at the newest build
//   - gh-<branch>-<unix timestamp>-<short sha>, unique to that one build
//
// The second form is what makes automatic updates work: because the tag changes
// with every build, a new build is a real change to the Deployment's pod
// template, which is what triggers the migration gate and then a rollout. The
// moving tag never changes, so Kubernetes sees no reason to replace any pods.
package version

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"oras.land/oras-go/v2/registry/remote"
	"oras.land/oras-go/v2/registry/remote/auth"
	"oras.land/oras-go/v2/registry/remote/retry"
)

// ErrNoMatchingTag is returned when the repository holds no build for the
// requested branch.
var ErrNoMatchingTag = errors.New("no image tag found for branch")

// unsafeBranchChars matches everything CI replaces with a dash when turning a
// branch name into a tag. Kept in sync with the compute-container-tags action.
var unsafeBranchChars = regexp.MustCompile(`[^a-zA-Z0-9-]`)

// SafeBranchName converts a git branch name into the form CI embeds in image
// tags, so "version-2026.8" becomes "version-2026-8".
func SafeBranchName(branch string) string {
	return unsafeBranchChars.ReplaceAllString(strings.TrimPrefix(branch, "refs/heads/"), "-")
}

// BranchTag is the moving tag CI republishes for every build of a branch.
func BranchTag(branch string) string {
	return "gh-" + SafeBranchName(branch)
}

// Credential authenticates against a registry.
type Credential struct {
	Username string
	Password string
}

// Empty reports whether the credential carries nothing to authenticate with,
// in which case the registry is accessed anonymously.
func (c Credential) Empty() bool {
	return c.Username == "" && c.Password == ""
}

// Request describes a tag to resolve.
type Request struct {
	// Repository is the fully qualified image repository to list tags in, for
	// example ghcr.io/goauthentik/server.
	Repository string
	Branch     string
	// Credential authenticates against the registry. Optional.
	Credential Credential
}

// Result is a resolved tag.
type Result struct {
	Tag string
	// BuildTime is when the build was published, from the tag's timestamp.
	// Zero for tags that do not carry one.
	BuildTime time.Time
	// Commit is the short commit SHA the build came from, if the tag carries
	// one.
	Commit string
}

// RegistryResolver resolves tags by listing them in the container registry.
type RegistryResolver struct {
	// Client is the HTTP client used to talk to the registry. Defaults to one
	// with retries, which matters because registries rate-limit aggressively.
	Client *http.Client

	// PlainHTTP talks to the registry over HTTP. For test registries only.
	PlainHTTP bool
}

// NewRegistryResolver returns a resolver with sane retry behavior.
func NewRegistryResolver() *RegistryResolver {
	return &RegistryResolver{Client: retry.DefaultClient}
}

// ResolveNewest lists the repository's tags and returns the newest build of the
// requested branch.
func (r *RegistryResolver) ResolveNewest(ctx context.Context, req Request) (Result, error) {
	if req.Branch == "" {
		return Result{}, errors.New("branch is required")
	}

	repo, err := r.repository(req)
	if err != nil {
		return Result{}, err
	}

	pattern := buildTagPattern(req.Branch)

	var newest Result
	// Tags are listed in lexical order, which is not build order: the
	// timestamps have the same width today but a tag list is not something to
	// rely on the ordering of. Scan everything and keep the newest.
	err = repo.Tags(ctx, "", func(tags []string) error {
		for _, tag := range tags {
			candidate, ok := parseTag(pattern, tag)
			if !ok {
				continue
			}
			if newest.Tag == "" || candidate.BuildTime.After(newest.BuildTime) {
				newest = candidate
			}
		}
		return nil
	})
	if err != nil {
		return Result{}, fmt.Errorf("failed to list tags in %q: %w", req.Repository, err)
	}

	if newest.Tag == "" {
		return Result{}, fmt.Errorf("%w: no %s-<timestamp>-<sha> tag in %q",
			ErrNoMatchingTag, BranchTag(req.Branch), req.Repository)
	}

	return newest, nil
}

// repository builds an authenticated client for one repository.
func (r *RegistryResolver) repository(req Request) (*remote.Repository, error) {
	if !strings.Contains(req.Repository, "/") {
		return nil, fmt.Errorf("repository %q must be fully qualified, e.g. ghcr.io/goauthentik/server", req.Repository)
	}

	repo, err := remote.NewRepository(req.Repository)
	if err != nil {
		return nil, fmt.Errorf("failed to parse repository %q: %w", req.Repository, err)
	}
	repo.PlainHTTP = r.PlainHTTP

	client := r.Client
	if client == nil {
		client = retry.DefaultClient
	}

	authClient := &auth.Client{
		Client: client,
		Cache:  auth.NewCache(),
	}
	if !req.Credential.Empty() {
		authClient.Credential = auth.StaticCredential(repo.Reference.Registry, auth.Credential{
			Username: req.Credential.Username,
			Password: req.Credential.Password,
		})
	}
	repo.Client = authClient

	return repo, nil
}

// buildTagPattern matches the per-build tags of one branch, capturing the
// timestamp and the commit. The branch is quoted, so the pattern is always
// valid however the branch is named.
func buildTagPattern(branch string) *regexp.Regexp {
	return regexp.MustCompile(fmt.Sprintf(`^%s-(\d+)-([0-9a-f]{7,40})$`,
		regexp.QuoteMeta(BranchTag(branch))))
}

// parseTag extracts the build metadata from a per-build tag.
func parseTag(pattern *regexp.Regexp, tag string) (Result, bool) {
	match := pattern.FindStringSubmatch(tag)
	if match == nil {
		return Result{}, false
	}

	seconds, err := strconv.ParseInt(match[1], 10, 64)
	if err != nil {
		return Result{}, false
	}

	return Result{
		Tag:       tag,
		BuildTime: time.Unix(seconds, 0).UTC(),
		Commit:    match[2],
	}, true
}
