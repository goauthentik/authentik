---
title: Writing documentation
---

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project.

## Set up your local build

Requirements:

-   Node.js 20 (or greater, we use Node.js 22)

The docs and the code are in the same Github repo, at https://github.com/goauthentik/authentik, so if you have cloned the repo, you already have the docs.

You can do local builds of the documentation to test your changes or review your new content, and to run the required `prettier` and linters before pushing your PR.

The documentation site is situated in the `/website` folder of the repo.

The site is built using npm, below are some useful make commands:

-   **Installation**: `make website-install`

    This command is required before running any of the following commands, and after upgrading any dependencies.

-   **Formatting**: `make website`, `make website-lint-fix`, or `npm run prettier`

    Run the appropriate formatting command for your set up before committing, to ensure consistent syntax, clean formatting, and verify links. Note that if the formatting command is not run, the build will fail with an error about linting.

-   **Live editing**: `make website-watch`

    For real time viewing of changes, as you make them.

:::info
Be sure to run a formatting command before committing changes.
:::

## Writing guidelines

Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

Whenever possible, use one of our [doc templates](./templates/index.md). This makes it a lot easier for you (no blank page frights!) and keeps the documentation consistent.

Make sure to add the new pages to the appropriate place in `/website/sidebars.js`. Otherwise, the content will not appear in the table of contents to the left.

Following the guidelines will make getting your PRs merged much easier and faster, with fewer edits needed. We appreciate our community contributors helping us keep the Docs consistent, easy-to-use, and high quality.

## Documentation for Integrations

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines.

For new integration documentation, please use the Integrations template in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

-   Make sure to add the service to a fitting category in `/website/sidebarsIntegrations.js`. If this is not done the service will not appear in the table of contents to the left.

-   For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

-   Try to order the documentation sections in an order that makes it easiest for the user to configure.
