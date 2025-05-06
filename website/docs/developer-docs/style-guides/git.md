---
title: Git, commits, and PR guidelines
---

# Git, commits, and PR guidelines

This document outlines the conventions for Git commits and pull requests in the authentik project.

## Commit messages

### Format

Use the format of `<package>: <verb> <description>`, where:

- `<package>` refers to the component being modified (see [authentik's structure](../architecture.md#authentik-server-structure))
- `<verb>` is an imperative verb describing the action (add, fix, update, etc.)
- `<description>` is a concise description of the change

Examples:
- `providers/saml2: fix parsing of requests`
- `website/docs: add config info for GWS`
- `stages/authenticator_totp: add support for custom issuer`

### Guidelines

- Begin with an imperative verb (add, fix, update, remove, etc.)
- Keep the first line under 72 characters
- Reference issues and pull requests after the first line
- Use the commit body to explain what and why, not how
- Separate the subject from the body with a blank line
- Naming of commits within a PR does not need to adhere to the guidelines as we squash merge PRs

Example of a well-formatted commit message:

```
flows: add ability to export and import flows

This adds API endpoints to export and import flows, including all
related stages and bindings. This makes it easier to move flows
between environments or to share them with others.

Fixes #1234
```

## Pull requests

### PR titles

Pull request titles should follow the same format as commit messages:

`<package>: <verb> <description>`

Examples:
- `providers/oauth2: add support for PKCE`
- `web: fix layout issues on mobile devices`

### PR descriptions

Your PR description should:

1. Explain the purpose of the changes
2. Link to any related issues using GitHub keywords like `Fixes #1234` or `Resolves #5678`
3. List any breaking changes or migration steps
4. Include screenshots for UI changes
5. Describe how to test the changes

### PR lifecycle

1. **Drafts** - Start PRs as drafts if they're not yet ready for review
2. **Reviews** - All PRs require at least one approval from a maintainer
3. **CI Checks** - All status checks must pass before merging
4. **Addressing Feedback** - Make requested changes and respond to comments
5. **Merging** - PRs are squash merged to keep the history clean

### PR best practices

- Keep PRs focused and reasonably sized
- Group related changes in a single PR
- Make sure tests cover the changes
- Update documentation alongside code changes
- Ensure all CI checks pass before requesting review
- Rebase your branch if conflicts arise

## Status checks

After you submit your pull request, verify that all status checks are passing. If a status check is failing, and you believe the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you.