---
name: community
description: >
    Route an authentik question to the right place and frame it so it gets answered: a bug
    goes to a GitHub Issue, a security problem to a private advisory, a usage question or
    early idea to GitHub Discussions or Discord, a docs problem to the docs issue form, and
    paid support to the Customer Portal. Use when someone asks "where do I report this",
    "is this a bug or am I holding it wrong", "I think I found a vulnerability", "I have a
    feature idea", "how do I get help", or "draft an issue for this". Opening a pull request
    belongs to contributing.
---

# authentik community and support

## Purpose

Each venue has one job. Issues are for defects and well-formed requests that maintainers will act on.
Questions go to Discussions or Discord. Vulnerabilities go to a private advisory rather than a public issue.
The wrong venue wastes maintainer time or, for security, exposes users before a fix exists.

Sources:

- `.github/ISSUE_TEMPLATE/`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `AI_POLICY.md`
- `website/docs/developer-docs/contributing.mdx`
- `website/docs/enterprise/enterprise-support.mdx`

## Decision tree

1. **Could it let someone gain access, data or privileges they shouldn't have?**
   Private security advisory:
   <https://github.com/goauthentik/authentik/security/advisories/new>. Not an issue,
   Discussion, Discord message or email. Check `SECURITY.md` "Intended functionality"
   first: expressions running Python, blueprints reading files, unescaped prompt HTML,
   token-free open redirects and unfiltered outgoing requests are by design.
2. **Is it a paid Enterprise customer needing support?** Customer Portal ticket at
   <https://customers.goauthentik.io/>. Never for vulnerabilities. Those still go to step 1.
3. **Is the documentation wrong, unclear or broken?** Issue with the "Documentation suggestion/problem" form.
4. **Does authentik do something wrong that you can reproduce on a supported version?**
   Issue with the "Bug report" form.
5. **Is it a feature you've thought through: the problem, the solution, the alternatives?**
   Issue with the "Feature request" form.
6. **Anything else**: "how do I…", "is this expected?", config help, an early idea.
   [GitHub Discussions](https://github.com/goauthentik/authentik/discussions) for
   something others will search for later; [Discord](https://goauthentik.io/discord) for
   quick back-and-forth.

Blank issues are disabled. The issue chooser offers only the three forms plus links to Discussions and Discord.

## What to include

**Security advisory** (from `SECURITY.md`):

- Affected versions.
- Steps to reproduce or a proof of concept.
- Impact: how it can be exploited and what it affects.
- Logs, configuration and suggested mitigations if you have them.
- Don't disclose publicly until the team has confirmed and fixed it. Don't request a CVE
  from another CNA. GitHub will assign it through the advisory.

**Bug report** (the form's fields):

- What happens, steps to reproduce, and what you expected.
- Deployment method: Docker, Kubernetes or AWS CloudFormation are the supported ones.
- The full version, including the patch number.
- Relevant log output from the server, worker or outpost, with secrets removed.
- Screenshots for UI bugs.
- For a server error, the `system_exception` event in the admin event log has a button
  that opens a prefilled issue with the stack trace.

**Feature request:** the problem it solves, the solution you want, the alternatives you
considered, and any context.

**Docs issue:** the exact page URL, what's wrong or missing, and a suggested fix.

**Discussions or Discord question:**

- Version and deployment method.
- What you're trying to achieve overall, as well as the step that failed.
- What you tried, what you expected, and what you saw, with logs.
- Relevant config (flow, provider or blueprint YAML) with secrets removed.

## Gotchas

- **Check the version first.** `SECURITY.md` lists the supported versions.
  A bug on an unsupported version should be retested on the latest patch release before filing.
- **AI-assisted reports need a human edit.** `AI_POLICY.md` requires that a person review
  and edit any AI-generated issue or discussion text, and maintainers close reports that
  look fully AI-driven. Trim generic text, check each claim against your own setup,
  and keep it short. If you're drafting for someone, hand them the draft to edit and submit.
  Don't file it for them.

- **Security announcements** come through the mailing list linked in `SECURITY.md` and the
  Discord server. Point people there instead of asking about an embargoed fix in public.
- **Email isn't for vulnerability reports.** `security@goauthentik.io` is for general
  security inquiries only.
