---
title: Writing documentation
---

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. Here are a few guidelines to ensure
the documentation is easy to read and uses similar phrasing.

## Setup

Requirements:

-   Node.js 16 (or greater)

The documentation site is situated in the `/website` folder of the authentik GitHub repository.

The site is built using npm, below are some useful make commands:

-   **Installation**: `make website-install`

    This command is required before running any of the following commands, and after upgrading any dependencies.

-   **Formatting**: `make website` or `make website-lint-fix`

    Run this command before committing, to ensure consistent syntax, clean formatting, and verify links. Note that if the formatting command is not run, the build will fail with an error about linting.

-   **Live editing**: `make website-watch`

    For real time viewing of changes, as you make them.

:::info
Be sure to run the formatter before committing changes.
:::

## Writing guidelines

Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation.

Following the guidelines will make getting your PRs merged much easier and faster, with fewer edits needed. We appreciate our community contributors helping us keep the Docs consistent, easy-to-use, and high quality.


## Documentation for Integrations

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines.

For new Integration documentation, please use the template in `/website/integrations/_template/service.md`.

-   Make sure to add the service to a fitting category in `/website/sidebarsIntegrations.js`. If you do not do this, the Integration will not appear in the Table of Contents to the left.

-   For placeholders, use angle brackets and italicize the text inside the brackets, to indicate that it is a variable (`_<placeholder-name>_`).

    Make sure to also define if the placeholder is something the user needs to define, is something another system defines, or is generated.

    If you're adding configuration snippets to the documentation, and the snippet is in a language that supports comments, other placeholders may be used, for example comments referencing an earlier step.

-   For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.
-   Try to order the documentation sections in an order that makes it easiest for the user to configure.
