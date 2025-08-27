---
title: Writing documentation
---

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation; everything from fixing a typo to adding additional content to writing a completely new topic.

The technical documentation (https://docs.goauthentik.io/docs/) and our integration guides (https://integrations.goauthentik.io/) are built, formatted, and tested using npm. The commands to build the content locally are defined in the `Makefile` in the root of the repository. Each command is prefixed with `docs-` or `integrations-` and corresponds to an NPM script within the `website` directory.

## Guidelines

Adhering to the following guidelines will help us get your PRs merged much easier and faster, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build-tools), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- After submitting a PR, you can view the Netlify Deploy Preview for the PR on GitHub, to check that your content rendered correctly, links work, etc. This is especially useful when using Docusaurus-specific features in your content.

- Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

- Remember to use our templates when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and they keep the documentation structure and headings consistent.
    - [docs templates](./templates/index.md)
    - [integration guide template](https://integrations.goauthentik.io/applications#add-a-new-application)

:::tip
If you encounter build check fails, or issues you with your local build, you might need to run `make docs-install` in order to get the latest build tools and dependencies; we do occasionally update our build tools.
:::

## Setting up a docs development environment

### Prerequisites

- [Node.js](https://nodejs.org/en) (24 or later)
- [Make](https://www.gnu.org/software/make/) (3 or later)

<Tabs defaultValue="macOS">
<TabItem value="macOS">

Install the required dependencies on macOS using Homebrew:

```shell
brew install node@24
```

</TabItem>
<TabItem value="Linux">

[Download NodeJS version 24](https://nodejs.org/en/download/current) for your Linux distribution.

</TabItem>
<TabItem value="Windows">

We're currently seeking community input on building the docs in Windows. If you have experience with this setup, please consider contributing to this documentation.

</TabItem>
</Tabs>

### Clone and fork the authentik repository

```shell
git clone https://github.com/goauthentik/authentik
```

The documentation, integration guides, API docs, and the code are in the same [GitHub repo](https://github.com/goauthentik/authentik), so if you have cloned and forked the repo, you already have the docs and integration guides.

### Set up your local build tools

Run the following command to install or update the build tools for both the technical docs and integration guides.

```shell
make docs-install
```

Installs or updates the build dependencies such as Docusaurus, Prettier, and ESLint. You should run this command when you are first setting up your writing environment, and also if you encounter build check fails either when you build locally or when you push your PR to the authentik repository. Running this command will grab any new dependencies that we might have added to our build tool package.

## Writing or modifying technical docs

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines about our technical documentation (https://docs.goauthentik.io/docs/):

- For new entries, make sure to add any new pages to the `/docs/sidebar.mjs` file.
  Otherwise, the new page will not appear in the table of contents to the left.

- Always be sure to run the `make docs` command on your local branch _before_ pushing the PR to the authentik repo. This command does important linting, and the build check in our repo will fail if the linting has not been done. In general, check on the health of your build before pushing to the authentik repo, and also check on the build status of your PR after you create it.

For our technical documentation (https://docs.goauthentik.io/docs/), the following commands are used:

### Build locally

```shell
make docs
```

This command is a combination of `make docs-lint-fix` and `make docs-build`. It is important to run this command before committing changes because linter errors will prevent the build checks from passing.

### Live editing

```shell
make docs-watch
```

Starts a local development server for the documentation site and opens a preview in your browser. This command will automatically rebuild your local documentation site in real time, as you write or make changes to the Markdown files in the `website/docs` directory.

## Writing or modifying integration guides

In addition to following the [Style Guide](./style-guide.mdx) please review the following guidelines about our integration guides (https://integrations.goauthentik.io/).

- For new integration documentation, please use the Integrations template in our [Github repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

- For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.

- Make sure to create a directory for your service in a fitting category within [`/website/integrations/`](https://github.com/goauthentik/authentik/tree/main/website/integrations).

:::tip Sidebars and categories
You no longer need to modify the integrations sidebar file manually. This is now automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
:::

When authoring integration guides, the following commands are used:

### Build locally

```shell
make integrations
```

This command is a combination of `make docs-lint-fix` and `make integrations-build`. This command should always be run on your local branch before committing your changes to a pull request to the authentik repo. It is important to run this command before committing changes because linter errors will prevent the build checks from passing.

### Live editing

```shell
make integrations-watch
```

Starts a local development server for the integrations site and opens a preview in your browser. This command will automatically rebuild your local integrations site in real time, as you write or make changes to the Markdown files in the `website/integrations` directory.
