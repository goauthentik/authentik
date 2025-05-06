---
title: Contributing to authentik
---

:+1::tada: Thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to authentik and its components, which are hosted in the [goauthentik Organization](https://github.com/goauthentik) on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

We appreciate contributions of code, documentation, enhancements, and bug fixes. Read more [below](#how-can-i-contribute) about the many ways to contribute.

## Code of Conduct

We expect all contributors to act professionally and respectfully in all interactions. If there's something you dislike or think can be done better, tell us! We'd love to hear any suggestions for improvement. todo(dominic): move our CODE_OF_CONDUCT.md to the website or vice-versa

## I don't want to read this whole thing I just have a question!!!

Either [create a question on GitHub](https://github.com/goauthentik/authentik/issues/new?assignees=&labels=question&template=question.md&title=) or join [the Discord server](https://goauthentik.io/discord?utm_source=docs&utm_campaign=a7k_contributing_docs_tldr)

## What should I know before I get started?

Before contributing to authentik, it's helpful to understand its components and structure. Check out the [architecture overview](./architecture.md) to learn about the different parts of the system.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for authentik. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

Whenever authentik encounters an error, it will be logged as an Event with the type `system_exception`. This event type has a button to directly open a pre-filled GitHub issue form.

This form will have the full stack trace of the error that occurred and shouldn't contain any sensitive data.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for authentik, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion and find related suggestions.

When you are creating an enhancement suggestion, please fill in [the template](https://github.com/goauthentik/authentik/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=), including the steps that you imagine you would take if the feature you're requesting existed.

### Your First Code Contribution

#### Local development

authentik can be run locally, all though depending on which part you want to work on, different pre-requisites are required.

This is documented in the [developer docs](./setup/index.md).

### Help with the Docs

Contributions to the technical documentation are greatly appreciated. Open a PR if you have improvements to make or new content to add. If you have questions or suggestions about the documentation, open an Issue. No contribution is too small.

Please be sure to refer to our [Documentation Style Guide](./style-guides/documentation.md) for the docs, and use a [template](./docs/templates/index.md) to make it easier for you. The style guidelines are also used for any Integrations documentation, and we have a template for Integrations as well, in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

### Pull Requests

The process described here has several goals:

- Maintain authentik's quality
- Fix problems that are important to users
- Working toward the best possible authentik

Please follow these steps to have your contribution considered by the maintainers:

1. Follow the [style guides](./style-guides/index.md)
2. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing <details><summary>What if the status checks are failing?</summary>If a status check is failing, and you believe that the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you. If we conclude that the failure was a false positive, then we will open an issue to track that problem with our status check suite.</details>
3. Ensure your Code has tests. While it is not always possible to test every single case, the majority of the code should be tested.

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Style guides

We have several style guides for different parts of the project: todo(dominic): link style guide index
