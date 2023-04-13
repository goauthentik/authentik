# Contributing to authentik

:+1::tada: Thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to authentik and its components, which are hosted in the [goauthentik Organization](https://github.com/goauthentik) on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

#### Table Of Contents

[Code of Conduct](#code-of-conduct)

[I don't want to read this whole thing, I just have a question!!!](#i-dont-want-to-read-this-whole-thing-i-just-have-a-question)

[What should I know before I get started?](#what-should-i-know-before-i-get-started)

-   [The components](#the-components)
-   [authentik's structure](#authentiks-structure)

[How Can I Contribute?](#how-can-i-contribute)

-   [Reporting Bugs](#reporting-bugs)
-   [Suggesting Enhancements](#suggesting-enhancements)
-   [Your First Code Contribution](#your-first-code-contribution)
-   [Help with the Docs](#help-with-the-docs)
-   [Pull Requests](#pull-requests)

[Styleguides](#styleguides)

-   [Git Commit Messages](#git-commit-messages)
-   [Python Styleguide](#python-styleguide)
-   [Documentation Styleguide](#documentation-styleguide)

## Code of Conduct

Basically, don't be a dickhead. This is an open-source non-profit project, that is made in the free time of Volunteers. If there's something you dislike or think can be done better, tell us! We'd love to hear any suggestions for improvement.

## I don't want to read this whole thing I just have a question!!!

Either [create a question on GitHub](https://github.com/goauthentik/authentik/issues/new?assignees=&labels=question&template=question.md&title=) or join [the Discord server](https://goauthentik.io/discord)

## What should I know before I get started?

### The components

authentik consists of a few larger components:

-   _authentik_ the actual application server, is described below.
-   _outpost-proxy_ is a Go application based on a forked version of oauth2_proxy, which does identity-aware reverse proxying.
-   _outpost-ldap_ is a Go LDAP server that uses the _authentik_ application server as its backend
-   _web_ is the web frontend, both for administrating and using authentik. It is written in TypeScript using lit-html and the PatternFly CSS Library.
-   _website_ is the Website/documentation, which uses docusaurus.

### authentik's structure

authentik is at it's very core a Django project. It consists of many individual django applications. These applications are intended to separate concerns, and they may share code between each other.

These are the current packages:
<a id="authentik-packages"/>

```
authentik
├── admin - Administrative tasks and APIs, no models (Version updates, Metrics, system tasks)
├── api - General API Configuration (Routes, Schema and general API utilities)
├── blueprints - Handle managed models and their state.
├── core - Core authentik functionality, central routes, core Models
├── crypto - Cryptography, currently used to generate and hold Certificates and Private Keys
├── events - Event Log, middleware and signals to generate signals
├── flows - Flows, the FlowPlanner and the FlowExecutor, used for all flows for authentication, authorization, etc
├── lib - Generic library of functions, few dependencies on other packages.
├── outposts - Configure and deploy outposts on kubernetes and docker.
├── policies - General PolicyEngine
│   ├── dummy - A Dummy policy used for testing
│   ├── event_matcher - Match events based on different criteria
│   ├── expiry - Check when a user's password was last set
│   ├── expression - Execute any arbitrary python code
│   ├── password - Check a password against several rules
│   └── reputation - Check the user's/client's reputation
├── providers
│   ├── ldap - Provide LDAP access to authentik users/groups using an outpost
│   ├── oauth2 - OIDC-compliant OAuth2 provider
│   ├── proxy - Provides an identity-aware proxy using an outpost
│   └── saml - SAML2 Provider
├── recovery - Generate keys to use in case you lock yourself out
├── root - Root django application, contains global settings and routes
├── sources
│   ├── ldap - Sync LDAP users from OpenLDAP or Active Directory into authentik
│   ├── oauth - OAuth1 and OAuth2 Source
│   ├── plex - Plex source
│   └── saml - SAML2 Source
├── stages
│   ├── authenticator_duo - Configure a DUO authenticator
│   ├── authenticator_static - Configure TOTP backup keys
│   ├── authenticator_totp - Configure a TOTP authenticator
│   ├── authenticator_validate - Validate any authenticator
│   ├── authenticator_webauthn - Configure a WebAuthn authenticator
│   ├── captcha - Make the user pass a captcha
│   ├── consent - Let the user decide if they want to consent to an action
│   ├── deny - Static deny, can be used with policies
│   ├── dummy - Dummy stage to test
│   ├── email - Send the user an email and block execution until they click the link
│   ├── identification - Identify a user with any combination of fields
│   ├── invitation - Invitation system to limit flows to certain users
│   ├── password - Password authentication
│   ├── prompt - Arbitrary prompts
│   ├── user_delete - Delete the currently pending user
│   ├── user_login - Login the currently pending user
│   ├── user_logout - Logout the currently pending user
│   └── user_write - Write any currenetly pending data to the user.
└── tenants - Soft tennancy, configure defaults and branding per domain
```

This django project is running in gunicorn, which spawns multiple workers and threads. Gunicorn is run from a lightweight Go application which reverse-proxies it, handles static files and will eventually gain more functionality as more code is migrated to go.

There are also several background tasks which run in Celery, the root celery application is defined in `authentik.root.celery`.

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

This is documented in the [developer docs](https://goauthentik.io/developer-docs/?utm_source=github)

### Help with the Docs
Contributions to the technical documentation are greatly appreciated. Open a PR if you have improvements to make or new content to add. If you have questions or suggestions about the documentation, open an Issue. No contribution is too small.

### Pull Requests

The process described here has several goals:

-   Maintain authentik's quality
-   Fix problems that are important to users
-   Engage the community in working toward the best possible authentik
-   Enable a sustainable system for authentik's maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow the [styleguides](#styleguides)
2. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing <details><summary>What if the status checks are failing?</summary>If a status check is failing, and you believe that the failure is unrelated to your change, please leave a comment on the pull request explaining why you believe the failure is unrelated. A maintainer will re-run the status check for you. If we conclude that the failure was a false positive, then we will open an issue to track that problem with our status check suite.</details>
3. Ensure your Code has tests. While it is not always possible to test every single case, the majority of the code should be tested.

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.

## Styleguides

### PR naming

-   Use the format of `<package>: <verb> <description>`
    -   See [here](#authentik-packages) for `package`
    -   Example: `providers/saml2: fix parsing of requests`

### Git Commit Messages

-   Use the format of `<package>: <verb> <description>`
    -   See [here](#authentik-packages) for `package`
    -   Example: `providers/saml2: fix parsing of requests`
-   Reference issues and pull requests liberally after the first line
-   Naming of commits within a PR does not need to adhere to the guidelines as we squash merge PRs

### Python Styleguide

All Python code is linted with [black](https://black.readthedocs.io/en/stable/), [PyLint](https://www.pylint.org/) and [isort](https://pycqa.github.io/isort/).

authentik runs on Python 3.9 at the time of writing this.

-   Use native type-annotations wherever possible.
-   Add meaningful docstrings when possible.
-   Ensure any database migrations work properly from the last stable version (this is checked via CI)
-   If your code changes central functions, make sure nothing else is broken.

### Documentation Styleguide

-   Use [MDX](https://mdxjs.com/) whenever appropriate.
