---
title: Writing documentation
---

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation; everything from fixing a typo to adding additional content to writing a completely new topic.

Adhering to the following guidelines will help us get your PRs merged much easier and faster, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

- Remember to use our [docs templates](./templates/index.md) when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and keeps the documentation structure and headings consistent.

- To test how the documentation renders you can build locally and then use the Netlify Deploy Preview, especially when using Docusaurus-specific features. You can also run the `make docs-watch` command on your local build, to see the rendered pages as you make changes.

- Be sure to run the `make docs` command on your local branch, before pushing the PR to the authentik repo. This command does important linting, and the build check in our repo will fail if the linting has not been done.

- For new entries, make sure to add any new pages to the appropriate `sidebar.js` file. Otherwise, the new page will not appear in the table of contents to the left.

## Set up your local build

Requirements:

- Node.js 20 (or greater, we use Node.js 24)

The docs and the code are in the same Github repo, at https://github.com/goauthentik/authentik, so if you have cloned the repo, you already have the docs.

You can do local builds of the documentation to test your changes or review your new content, and to run the required `make docs` command (which runs `prettier` and other linters) before pushing your PR.

The documentation site is situated in the `/website` folder of the repo.

The site is built using npm, below are some useful make commands:

- **Installation**: `make docs-install`

    This command is required before running any of the following commands, and after upgrading any dependencies.

- **Formatting**: `make docs`, `make docs-lint-fix`, or `npm run prettier`

    Run the appropriate formatting command for your set up before committing, to ensure consistent syntax, clean formatting, and verify links. Note that if the formatting command is not run, the build will fail with an error about linting.

- **Live editing**: `make docs-watch`

    For real-time viewing of changes, as you make them.

:::info
Be sure to run a formatting command before committing changes.
:::

## Documentation for integrations

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines.

For new integration documentation, please use the Integrations template in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

- For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

- Try to order the documentation sections in an order that makes it easiest for the user to configure.
