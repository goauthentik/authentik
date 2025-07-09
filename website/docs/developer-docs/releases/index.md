# Releasing authentik

### Creating a standard release

- Ensure a branch exists for the version family (for 2022.12.2 the branch would be `version-2022.12`)
- Merge all the commits that should be released on the version branch

    If backporting commits to a non-current version branch, cherry-pick the commits.

- Check if any of the changes merged to the branch make changes to the API schema, and if so update the package `@goauthentik/api` in `/web`
- Push the branch, which will run the CI pipeline to make sure all tests pass
- Create the version subdomain for the version branch ([see](https://github.com/goauthentik/terraform/commit/87792678ed525711be9c8c15dd4b931077dbaac2)) and add the subdomain in Netlify ([here](https://app.netlify.com/sites/authentik/settings/domain))
- Create/update the release notes

    #### For initial releases:
    - Copy `docs/docs/releases/_template.md` to `docs/docs/releases/v2022.12.md` and replace `xxxx.x` with the version that is being released

    - Fill in the section of `Breaking changes` and `New features`, or remove the headers if there's nothing applicable

    - Run `git log --pretty=format:'- %s' version/2022.11.3...version-2022.12`, where `version/2022.11.3` is the tag of the previous stable release. This will output a list of all commits since the previous release.

    - Paste the list of commits since the previous release under the `Minor changes/fixes` section.

        Run `make gen-changelog` and use the contents of `changelog.md`. Remove merged PRs from bumped dependencies unless they fix security issues or are otherwise notable. Remove merged PRs with the `docs/` prefix.

    - Sort the list of commits alphabetically and remove all commits that have little importance, like dependency updates and linting fixes

    - Run `make gen-diff` and copy the contents of `diff.md` under `API Changes`

    - Run `make docs`

    #### For subsequent releases:
    - Paste the list of commits since the previous release into `docs/releases/v2022.12.md`, creating a new section called `## Fixed in 2022.12.2` underneath the `Minor changes/fixes` section

    - Run `make gen-changelog` and use the contents of `changelog.md`. Remove merged PRs from bumped dependencies unless they fix security issues or are otherwise notable. Remove merged PRs with the `docs/` prefix.

    - Run `make gen-diff` and copy the contents of `diff.md` under `API Changes`, replacing the previous changes

    - Run `make docs`

- Run `bumpversion` on the version branch with the new version (i.e. `bumpversion --new-version 2022.12.2 minor --verbose`)
- Push the tag and commit
- A GitHub actions workflow will start to run a last test in container images and create a draft release on GitHub
- Edit the draft GitHub release
    - Make sure the title is formatted `Release 2022.12.0`
    - Add the following to the release notes

        ```
        See https://goauthentik.io/docs/releases/2022.12
        ```

        Or if creating a subsequent release

        ```
        See https://goauthentik.io/docs/releases/2022.12#fixed-in-2022121
        ```

    - Auto-generate the full release notes using the GitHub _Generate Release Notes_ feature

### Preparing a security release

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

    Include the new file in the `/website/docs/sidebars.js`

    Push the branch to https://github.com/goauthentik/authentik-internal for CI to run and for reviews

    An image with the fix is built under `ghcr.io/goauthentik/internal-server` which can be made accessible to the reporter for testing

- Check with the original reporter that the fix works as intended
- Wait for GitHub to assign a CVE
- Announce the release of the vulnerability via Mailing list and discord

<details>
<summary>Mailing list template</summary>

Subject: `Notice of upcoming authentik Security releases 2022.10.3 and 2022.11.3`

```markdown
We'll be publishing a security Issue (CVE-2022-xxxxx) and accompanying fix on _date_, 13:00 UTC with the Severity level High. Fixed versions x, y and z will be released alongside a workaround for previous versions. For more info, see the authentik Security policy here: https://goauthentik.io/docs/security/policy.
```

</details>

<details>
<summary>Discord template</summary>

```markdown
@everyone We'll be publishing a security Issue (CVE-2022-xxxxx) and accompanying fix on _date_, 13:00 UTC with the Severity level High. Fixed versions x, y and z will be released alongside a workaround for previous versions. For more info, see the authentik Security policy here: https://goauthentik.io/docs/security/policy.
```

</details>

### Creating a security release

- On the date specified in the announcement, retag the image from `authentik-internal` to the main image:

    ```
    docker buildx imagetools create -t ghcr.io/goauthentik/server:xxxx.x ghcr.io/goauthentik/internal-server:gh-cve-2022-xxx
    docker buildx imagetools create -t ghcr.io/goauthentik/server:xxxx.x.x ghcr.io/goauthentik/internal-server:gh-cve-2022-xxx
    ```

    Where xxxx.x is the version family and xxxx.x.x is the full version.

    This will make the fixed container image available instantly, while the full release is running on the main repository.

- Push the local `security/CVE-2022-xxxxx` branch into a PR, and squash merge it if the pipeline passes
- If the fix made any changes to the API schema, merge the PR to update the web API client
- Cherry-pick the merge commit onto the version branch
- If the fix made any changes to the API schema, manually install the latest version of the API client in `/web`
- Resume the instructions above, starting with the `bumpversion` step
- After the release has been published, update the Discord announcement and send another mail to the mailing list to point to the new releases

<details>
<summary>Mailing list template</summary>

Subject: `Release of authentik Security releases 2022.10.3 and 2022.11.3`

```markdown
The security advisory for CVE-2022-xxxxx has been published: https://github.com/goauthentik/authentik/security/advisories/GHSA-mjfw-54m5-fvjf

Releases 2022.10.3 and 2022.11.3 with fixes included are available here: https://github.com/goauthentik/authentik/releases
```

</details>

<details>
<summary>Discord template</summary>

```markdown
[...existing announcement...]

Edit:

Advisory for for CVE-2022-xxxxx has been published here https://github.com/goauthentik/authentik/security/advisories/GHSA-mjfw-54m5-fvjf

The fixed versions 2022.10.3 and 2022.11.3 are available here: https://github.com/goauthentik/authentik/releases
```

</details>
