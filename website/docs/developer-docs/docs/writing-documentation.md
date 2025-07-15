---
title: Writing documentation
---

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation; everything from fixing a typo to adding additional content to writing a completely new topic.

## Guidelines

To test how the documentation renders you can build locally and then use the Netlify Deploy Preview, especially when using Docusaurus-specific features.
Adhering to the following guidelines will help us get your PRs merged much easier and faster, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- Remember to use our [docs templates](./templates/index.md) when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and keeps the documentation structure and headings consistent.

## authentik documentation

### Set up your local build

The docs and the code are in the same [GitHub repo](https://github.com/goauthentik/authentik), so if you have cloned the repo, you already have the docs.

You can do local builds of the documentation to test your changes or review your new content, and to run the required `make docs` command (which runs `prettier` and other linters) before pushing your PR.

Requirements:

- Node.js 24 (or greater)

Commands to build the documentation locally are defined in the `Makefile` in the root of the repository.
Each command is prefixed with `docs-` and corresponds to an NPM script within the `website` directory.

#### `make docs-install`

Installs the build dependencies such as Docusaurus, Prettier, and ESLint.
You should run this command after pulling any new changes to your fork of the authentik repository.

### Live editing

For new entries, make sure to add any new pages to the appropriate `sidebar.mjs` file.
Otherwise, the new page will not appear in the table of contents to the left.

#### `make docs-watch`

Starts a development server for the documentation site.
This command will automatically rebuild the documentation site whenever you make changes to the Markdown (MDX) files in the `website/docs` directory.

### Formatting

Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

Note that linter errors will prevent the build from passing, so it is important to run this command before committing changes.

#### `make docs-lint-fix`

Applies formatting and code style fixes via Prettier and ESLint.

This command will automatically apply most fixes to the documentation, but any fixes that cannot be applied will be reported as warnings.

### Build

#### `make docs-build`

Builds the documentation site for production deployment.

#### `make docs`

A combination of `make docs-lint-fix` and `make docs-build`.
This command is useful before committing your changes to a pull request.

Be sure to run the `make docs` command on your local branch before pushing the PR to the authentik repo.

## Integrations

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines.

For new integration documentation, please use the Integrations template in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

- For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

Make sure to create a directory for your service in a fitting category within [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations).

:::tip Sidebars and categories
You no longer need to modify the integrations sidebar file manually. This is now automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
:::

### Live editing

#### `make docs-integrations-watch`

Starts a development server for the integrations guides.
This command will automatically rebuild the documentation site whenever you make changes to the Markdown (MDX) files in the [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations) directory.

### Build

#### `make docs-integrations-build`

Builds the integrations guides for production deployment.

## API documentation

The API documentation is built using the [OpenAPI plugin](https://github.com/PaloAltoNetworks/docusaurus-openapi-docs) for Docusaurus.
To build the API documentation, you need to have Docker installed on your machine.

### Live editing

#### `make docs-api-watch`

Generates Markdown files from the OpenAPI schema and starts a development server for the API documentation.

### Build

#### `make docs-api-build`

Generates Markdown files from the OpenAPI schema and builds the API documentation for production deployment.
