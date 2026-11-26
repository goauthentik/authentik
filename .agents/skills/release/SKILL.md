---
name: release
description: >
    Run an authentik release as release manager: feature freeze, translations and WebAuthn
    metadata, branch-off, backports, the generated changelog and API diff, release
    candidates, the final release, and the follow-up PRs. Use for requests like "tag RC1",
    "tag the release", "branch off 2026.11", "the release workflow failed", "generate the
    changelog", "publish the draft release", "ping the beta testers", or "what's next on the
    release checklist". For release managers. It needs maintainer access to GitHub Actions,
    Netlify, and the internal Notion release pages.
---

# authentik release management

## Purpose

A release spans a few weeks of checklist work and a handful of GitHub Actions. Most of it is
routine, but several steps fail in ways that are easy to misread, and a few are hard to undo
because they publish tags, images or messages. This skill walks the release in order and
calls out the traps found in past releases.

The release manager's Notion pages hold the internal plan: the per-release page
(the dated checklist) and the release task created from the **Release xxxx.xx** template
(the per-version steps). Read both first. Where this skill and Notion disagree, ask the
release manager and fix whichever is stale.

## When to invoke

- "What's next on the release checklist?"
- "Run the translation sync", "update the WebAuthn MDS blob", "branch off."
- "Generate the changelog / API diff for 2026.11.0."
- "Tag RC1", "tag 2026.11.0", "the tag workflow failed."
- "Publish the draft release", "write the beta-tester announcement."

Not this skill: normal PR conventions or running the test suites (see AGENTS.md).

## Ground rules

- **Ask before anything outward-facing.** A tag workflow dispatch, a published release,
  and a Discord or Slack post all reach people outside the session. Confirm each one with
  the release manager, every time.
- **Report what happened, from the PR states.** When closing or merging a batch of PRs, check each
  PR's final state (`merged` vs `closed`, and by whom). Someone else may have merged one
  before you got to it.
- **Before a force-push**, `git fetch` and check `git log HEAD..origin/<branch>` for
  teammates' commits.
- **Recompute the dates.** The checklist is written as D-minus-N days from the release
  date. If the schedule slips, work out where you are from the finished steps. The date
  printed next to a step is out of date by then.

## Workflow

Steps are tagged: `[gh]` GitHub UI or `gh`, `[shell]` local command, `[verify]` check before
moving on, `[ask]` confirm with the release manager first.

### 1. Before branch-off

1. **[gh]** Every item in the release's "Required" GitHub milestone is done or explicitly
   moved.
2. **[gh]** Run **Translation - Extract and compile** on `main` and merge its PR.
3. **[gh]** Transifex sync (a maintainer starts it, with a 60% threshold). It opens one PR
   per language.
    - Approve and merge them all. If one fails CI, turn on auto-merge and rerun the failed
      jobs (`gh run rerun <id> --failed`). Flaky e2e jobs are the common cause.
    - Then run **Translation - Extract and compile** again and merge the
      `core, web: update translations` PR.
4. **[gh]** Run **Gen - Webauthn MDS** and merge the `stages/authenticator_webauthn` PR
   from the automation account.
5. **[gh]** Merge the release notes PR (`website/docs/releases/<year>/v<year>.<minor>/index.mdx`,
   front matter `beta: true`).

### 2. Branch-off

1. **[ask][gh]** Run **Release - Branch-off** with the **next** version (for example
   `2027.2` when releasing 2026.11). It creates `version-<year>.<minor>` and a version-bump
   PR for `main`. Merge that PR.
2. From now on, fixes reach the release by backport: add the
   `backport/version-<year>.<minor>` label and the cherry-pick bot opens the PR. Watch for
   failed cherry-picks. Those need a manual PR.
3. Tell the team that branch-off happened so feature merges to `main` can resume.

### 3. Generate the changelog and API diff

The release notes page imports two generated partials: `_changelog.mdx` and
`_api-changes.mdx`, next to `index.mdx`.

1. **[shell]** Check out the release branch: the script refuses to write from any other
   branch. A worktree keeps your main checkout free:
   `git worktree add ../ak-release version-2026.11`, then link or install `node_modules`.
2. **[shell]** `make gen-changelog version=2026.11.0` (add `review=1` to print instead of
   write).
3. **[shell]** `make gen-diff version=2026.11.0`. This needs Docker running.
4. **[verify]** Skim the output. The script already:
    - Drops `ci:` and `website` entries, and commits already cherry-picked into the
      previous release.
    - Drops Dependabot updates (`bump X from A to B`, `bump the X group`) from `.0`
      releases, but keeps them in patch releases, and keeps `security:` entries and any
      that name a CVE or GHSA.
    - Collapses translation commits into one entry, merges duplicate subjects, and sorts.
    - Escapes everything through a Markdown serializer, so commit subjects can't inject
      markup.
5. **[gh]** Commit the partials on a branch off `main` and label it for backport. Regenerate
   them before the final release to pick up late backports.

**Gotchas:** a patch release adds its own `## Fixed in <version>` section, so rerunning it
is safe. Title CVE fixes `security: …`. It's the only way they survive the `.0` filter.

### 4. Release candidates

1. **[verify]** Before tagging, make sure the release branch builds the way the release
   does. The release builds the Rust proxy outpost with
   `--no-default-features --features proxy`, which PR CI on `main` may not cover. Run
   `make ci-lint-clippy-proxy` if the target exists, or that `cargo clippy` command
   directly. Code that only the server uses must sit behind
   `#[cfg(feature = "core")]`.
2. **[verify]** Check that the release branch is quiet: backport PRs have auto-merge off.
   The tag workflow commits a version bump and pushes it. If the branch moves mid-run, the
   push is rejected and the run fails.
3. **[ask][gh]** Run **Release - Tag new version** on `version-<year>.<minor>` with
   version `<year>.<minor>.0-rcN` and release reason `prerelease`.
4. **[verify]** When it finishes, check the tag exists (`git ls-remote --tags origin`),
   the draft release has every binary and image archive, and the proxy jobs passed.

**When the tag workflow fails:**

- **Before the tag exists** (for example the version-bump push was rejected): the run
  published no tag, images or release. Fix the cause and dispatch again with the same
  version.
- **After images were pushed but before the tag**: container images for that rc already
  exist. Don't reuse the number. Move to the next rc.
- Read the failing job's log first (`gh run view <id> --log-failed`). Don't guess from the
  job name.

### 5. Publish the draft release

1. **[gh]** Make the description match earlier releases:

    ```
    See https://next.goauthentik.io/releases/<year>.<minor>

    ## What's Changed
    * <PR title> by @<author> in <PR URL>

    **Full Changelog**: https://github.com/goauthentik/authentik/compare/<previous tag>...<this tag>
    ```

    The workflow only writes the first line. For later rcs, list the PRs merged into the
    release branch since the previous rc.

2. **[verify]** Open the release notes link. **Don't publish until it loads.** The `next`
   docs site is built from the `next` branch. **Release - Update next branch** force-pushes
   that branch from `main` daily at noon UTC. Netlify can skip or fail that build without
   a GitHub status. If the page 404s, trigger "Clear cache and deploy site" on the docs
   site in Netlify. Use `/releases/<year>.<minor>`, not `/docs/releases/…` (that redirects).
3. **[ask][gh]** Publish. For an rc, keep it a prerelease and leave "Set latest version"
   off: `gh release edit <tag> --draft=false --prerelease --latest=false`.

### 6. Announce an rc and smoke-test it

1. **[ask]** The release manager posts in Discord `#beta-testers`, pinging `@beta-testers`.
   Draft the message from the release notes' **Highlights** and **Breaking changes**
   sections: a line on what this rc fixes, a short emoji list of highlights, a breaking-
   changes warning that lists the ones most likely to bite, the release-notes link,
   `AUTHENTIK_TAG=<version> docker compose up -d`, and the planned date. Stay under
   Discord's 2,000-character limit.
2. **[shell]** Smoke-test the published images with the release branch's
   `lifecycle/container/compose.yml` in a scratch directory. Generate `PG_PASS` and
   `AUTHENTIK_SECRET_KEY` into `.env`. Set `COMPOSE_PORT_HTTP`/`COMPOSE_PORT_HTTPS` if a
   dev server already holds 9000/9443. Run with a project name (`-p ak-rc`).
3. **[verify]** All three containers report healthy and migrations applied. Start setup at
   `http://<host>:<port>/`: going straight to `/if/flow/initial-setup/` shows "Access
   denied" by design.

### 7. Final release and after

1. Before the release date, check the release candidate feedback (Discord, GitHub issues
   mentioning the rc), confirm no blockers, and get the team's go-ahead.
2. **[shell]** Regenerate the changelog and diff partials (step 3).
3. **[ask][gh]** Tag `<year>.<minor>.0` with release reason `feature` (patches:
   `bugfix`, security releases: `security`). Publish with "Set latest version" on.
4. **[gh]** Merge the version bump PRs in the version repo and the Helm chart repo. If
   they fail, wait for the On Publish workflow to finish building images, then retry.
5. **[gh]** Update `SECURITY.md` supported versions (add the new one, drop the oldest) and
   backport it.
6. **[gh]** Point Netlify's default docs branch at the new release and rebuild.
7. Monitor GitHub and Discord, and schedule the retrospective.

## Other traps

- **Dependabot PR cleanup:** closing a batch is fine, but check each one's state first.
  `@dependabot ignore` comments on an already-merged PR still register, so leave them off
  merged PRs.
- **The release branch drifts from `main`:** after branch-off, every fix needs its
  backport label. Before each rc, list open PRs against the release branch and labeled
  PRs on `main` that have no cherry-pick yet.
- **CI action upgrades can change release builds:** a toolchain action that starts denying
  warnings only shows up when the release workflow first builds a feature combination PR CI
  doesn't. Read upgrade notes for actions used by `release-tag.yml`.
