# Release authentik

### Create a standard release

The release workflows are the source of truth for version branches, version bumps, tags, and artifacts. Do not run `bumpversion` or create release tags manually.

1. Confirm that the `version-<year>.<month>` branch exists and includes every change intended for the release. Use the matching `backport/version-<year>.<month>` label for backports.
2. Wait for CI on the version branch to pass.
3. Create or update the release notes:
    - For an initial release, copy `website/docs/releases/_template.md` to the matching year directory, such as `website/docs/releases/2026/v2026.8.md`.
    - For a patch release, add a `Fixed in <version>` section to the existing version-family page.
    - Run `make gen-changelog` and curate `changelog.md`. Remove routine dependency, lint, and documentation-only commits unless they are notable.
    - Run `make gen-diff` and add the generated API changes where applicable.
    - Run `make docs` and review the rendered release notes.
4. From GitHub Actions, run **Release - Tag new version** with the full version and release reason. The workflow validates the version, runs `make bump`, regenerates API clients, commits the version change, builds and tests artifacts, creates the `version/<version>` tag, and creates the GitHub release.
5. Review the generated GitHub release and its changelog link before publishing it. Publishing triggers the release workflow that distributes container and documentation images and updates the version and Helm repositories.

Use **Release - Branch-off** when starting a new version family. It creates the current version branch and backport label, then opens the pull request that bumps `main` to the next release candidate.

### Prepare a security release

- Create a draft GitHub Security advisory

<details>
<summary>Template</summary>

```markdown
### Summary

Short summary of the issue

### Patches

authentik x, y and z fix this issue, for other versions the workaround below can be used.

### Impact

Describe the impact that this issue has

### Details

Further explain how the issue works

### Workarounds

Describe a workaround if possible

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io).
```

</details>

- Request a CVE via the draft advisory
- If possible, add the original reporter in the advisory
- Implement a fix on a local branch `security/CVE-...`

    The fix must include unit tests to ensure the issue can't happen again in the future

    Update the release notes as specified above, making sure to address the CVE being fixed

    Create a new file `/website/docs/security/CVE-....md` with the same structure as the GitHub advisory

    Include the new file in the `/website/sidebars.js`

    Push the branch to https://github.com/goauthentik/authentik-internal for CI to run and for reviews

    An image with the fix is built under `ghcr.io/goauthentik/internal-server` which can be made accessible to the reporter for testing

- Check with the original reporter that the fix works as intended
- Wait for GitHub to assign a CVE
- Announce the release of the vulnerability via mailing list and Discord

<details>
<summary>Mailing list template</summary>

Subject: `Notice of upcoming authentik security releases <versions>`

```markdown
We will publish a security issue (`CVE-YYYY-NNNNN`) and its fix on _date_ at 13:00 UTC with _severity_. Fixed versions will be released alongside a workaround for previous versions. For details, see the [authentik security policy](/security/policy/).
```

</details>

<details>
<summary>Discord template</summary>

```markdown
@everyone We will publish a security issue (`CVE-YYYY-NNNNN`) and its fix on _date_ at 13:00 UTC with _severity_. Fixed versions will be released alongside a workaround for previous versions. For details, see the [authentik security policy](/security/policy/).
```

</details>

### Create a security release

- On the date specified in the announcement, retag the image from `authentik-internal` to the main image:

    ```
    docker buildx imagetools create -t ghcr.io/goauthentik/server:VERSION_FAMILY ghcr.io/goauthentik/internal-server:INTERNAL_TAG
    docker buildx imagetools create -t ghcr.io/goauthentik/server:VERSION ghcr.io/goauthentik/internal-server:INTERNAL_TAG
    ```

    Replace `VERSION_FAMILY`, `VERSION`, and `INTERNAL_TAG` with the release values.

    This will make the fixed container image available instantly, while the full release is running on the main repository.

- Push the local `security/CVE-YYYY-NNNNN` branch into a PR, and squash merge it if the pipeline passes
- Cherry-pick the merge commit onto the version branch
- Run **Release - Tag new version** for each fixed version. The workflow bumps versions and regenerates API clients.
- After the release has been published, update the Discord announcement and send another mail to the mailing list to point to the new releases

<details>
<summary>Mailing list template</summary>

Subject: `Release of authentik security releases <versions>`

```markdown
The security advisory for `CVE-YYYY-NNNNN` has been published: `<advisory_url>`

The fixed releases are available from the [authentik releases page](https://github.com/goauthentik/authentik/releases).
```

</details>

<details>
<summary>Discord template</summary>

```markdown
[...existing announcement...]

Edit:

The advisory for `CVE-YYYY-NNNNN` is available at `<advisory_url>`.

The fixed releases are available from the [authentik releases page](https://github.com/goauthentik/authentik/releases).
```

</details>
