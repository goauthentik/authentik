---
title: Writing documentation
---

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation; everything from fixing a typo to adding additional content to writing a completely new topic.

## Guidelines

To test how the documentation renders you can build locally and then use the Netlify Deploy Preview, especially when using Docusaurus-specific features.
Adhering to the following guidelines will help us get your PRs merged much easier and faster, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

- Remember to use our templates when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and they keep the documentation structure and headings consistent.
    - [docs templates](./templates/index.md)
    - integration guide template

- For new entries, make sure to add any new pages to the appropriate `sidebar.mjs` file.
  Otherwise, the new page will not appear in the table of contents to the left.

- Finally, be sure to run the `make docs` command on your local branch, _before_ pushing the PR to the authentik repo. This command does important linting, and the build check in our repo will fail if the linting has not been done. In general, check on the health of your build before pushing to the authetnik repo, and also check on the build status of your PR after you create it.

:::tip
If you encounter build check fails, or issues you with your local build, you might need to run `make docs-install` in order to get the latest build tools and dependencies; we do occasionally update our build tools.
:::

## Set up your local build

The documentation, ntegratins guides, API docs, and the code are in the same [GitHub repo](https://github.com/goauthentik/authentik), so if you have cloned the repo, you already have the docs.

You can do local builds of the documentation, integration guide, and API docs in order to test your changes or review your new content, and to run the required `make` commands (which runs `prettier` and other linters) before pushing your PR to the authetnik repository.

Requirements:

- Node.js 24 (or later)

## Technical docs

If you are contributing content to our technical documentation (https://docs.goauthentik.io/docs/)

The docs site is built using npm, and the commands to build the documentation locally are defined in the `Makefile` in the root of the repository. Each command is prefixed with `docs-` and corresponds to an NPM script within the `website` directory.

- **Install (or update) the build tools**: `make docs-install`

    Installs the build dependencies such as Docusaurus, Prettier, and ESLint. You should run this command after pulling any new changes to your fork of the authentik repository.

- **Build locally**: `make docs`

    This command is a combination of `make docs-lint-fix` and `make docs-build`. This command should always be run on your local branch before committing your changes to a pull request to the authentik repo.

- **Live editing**: `make docs-watch`

    Starts a development server for the documentation site. This command will automatically rebuild the documentation site whenever you make changes to the Markdown (MDX) files in the `website/docs` directory.

- **Formatting**: `make docs-lint-fix`

    Applies formatting and code style fixes via Prettier and ESLint. This command will automatically apply most fixes to the documentation, but any fixes that cannot be applied will be reported as warnings. It is important to run this command before committing changes, because linter errors will prevent the build checks from passing.

- **Build without running linters**: `make docs-build`

    Builds the documentation site for production deployment.

## Integration Guides

The Integrations site is built using npm, and the commands to build the documentation locally are defined in the `Makefile` in the root of the repository. Each command is prefixed with `docs-integrations-` and corresponds to an NPM script within the `website` directory.

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines about our integration guides.

- For new integration documentation, please use the Integrations template in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

- For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

- Make sure to create a directory for your service in a fitting category within [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations).

:::tip Sidebars and categories
You no longer need to modify the integrations sidebar file manually. This is now automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
:::

- **Live editing**: `make docs-integrations-watch`

    Starts a development server for the integrations guides. This command will automatically rebuild the documentation site whenever you make changes to the Markdown (MDX) files in the [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations) directory.

- **Build the Integrations site**: `make docs-integrations-build`

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
