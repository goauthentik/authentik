---
title: Writing documentation
---

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

Writing documentation for authentik is a great way for both new and experienced users to improve and contribute to the project. We appreciate contributions to our documentation; everything from fixing a typo to adding additional content to writing a completely new topic.

The [technical documentation](https://docs.goauthentik.io) and our [integration guides](https://integrations.goauthentik.io/) are built, formatted, and tested using `npm`. The commands to build the content locally are defined in the `Makefile` in the root of the repository. Each command is prefixed with `docs-` or `integrations-` and corresponds to an NPM script within the `website` directory.

## Documentation subdomains

authentik documentation is deployed to different subdomains based on the git branch:

| Subdomain                                          | Git Branch       | Description                      |
| -------------------------------------------------- | ---------------- | -------------------------------- |
| [main.goauthentik.io](https://main.goauthentik.io) | `main`           | Latest changes and features      |
| [next.goauthentik.io](https://next.goauthentik.io) | `next`           | Upcoming release content         |
| [docs.goauthentik.io](https://docs.goauthentik.io) | Current release  | Official stable documentation    |
| version-YYYY-MM.goauthentik.io                     | Specific release | Historical version documentation |

## Guidelines

Adhering to the following guidelines will help us get your PRs merged much easier and faster, with fewer edits needed.

- Ideally, when you are making contributions to the documentation, you should fork and clone our repo, then [build it locally](#set-up-your-local-build-tools), so that you can test the docs and run the required linting and spell checkers before pushing your PR. While you can do much of the writing and editing within the GitHub UI, you cannot run the required linters from the GitHub UI.

- After submitting a PR, you can view the Netlify Deploy Preview for the PR on GitHub, to check that your content rendered correctly, links work, etc. This is especially useful when using Docusaurus-specific features in your content.

- Please refer to our [Style Guide](./style-guide.mdx) for authentik documentation. Here you will learn important guidelines about not capitalizing authentik, how we format our titles and headers, and much more.

- Remember to use our templates when possible; they are already set up to follow our style guidelines, they make it a lot easier for you (no blank page frights!), and they keep the documentation structure and headings consistent.
    - [docs templates](./templates/index.md)
    - [integration guide template](https://integrations.goauthentik.io/applications#add-a-new-application)

:::tip
If you encounter build check fails, or issues with your local build, you might need to run `make docs-install` in order to get the latest build tools and dependencies; we do occasionally update our build tools.
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

- For new integration documentation, please use the Integrations template in our [GitHub repo](https://github.com/goauthentik/authentik) at `/website/integrations/template/service.md`.

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

## Developing the glossary

The [authentik glossary](/core/glossary/) provides definitions for both industry-standard terms (like LDAP, OAuth2, SAML) and authentik-specific concepts (like Flows, Stages, Blueprints).

### Adding a new glossary term

1. Create a new `.mdx` file in `website/docs/core/glossary/terms/` (e.g., `my-term.mdx`).

2. Add frontmatter with the required metadata:

```mdx
---
title: My Term
sidebar_custom_props:
    termName: My Term
    tags:
        - Category Name
    authentikSpecific: true # Only for authentik-specific terms
    shortDescription: Brief one-line description.
    longDescription: Detailed explanation with context, use cases, and examples.
---
```

### Glossary metadata fields

- **`termName`** (required): The display name of the term
- **`tags`** (required): Array of category tags for organizing terms. Common tags include:
    - Core Concepts
    - Flows
    - OAuth2/OIDC
    - SAML
    - Directory
    - Configuration
    - Protocols
- **`authentikSpecific`** (optional): Set to `true` for authentik-specific terms. This displays an "authentik specific" badge next to the term name to distinguish it from industry-standard terminology. Omit this field for industry-standard terms.
- **`shortDescription`** (required): Concise one-line summary displayed in the main glossary view
- **`longDescription`** (optional): Detailed explanation shown when users expand the term

### Formatting guidelines

- Use backticks for inline code: \`application\`
- Keep `shortDescription` to one sentence
- In `longDescription`, you can use multiple paragraphs separated by blank lines

## Page routing and URLs

Every documentation page you see on our website starts as a simple Markdown file in our repository. When you create or edit these files, our build system automatically transforms them into web pages with predictable URLs.

### Converting file paths to URLs

Let's take a look at the file path of the [Style Guide page](https://docs.goauthentik.io/developer-docs/docs/style-guide/):

```text
/website/docs/developer-docs/docs/style-guide.mdx
```

Compared to the URL path of this page, there are a few differences:

- The `website/docs` prefix is dropped.
- File extensions are removed.
- A trailing slash is added.

This results in the following URL path:

```text
https://docs.goauthentik.io/developer-docs/docs/style-guide/
```

The final published URL is made possible with a combination of [Docusaurus's routing system](https://docusaurus.io/docs/advanced/routing) and [Netlify's redirects](https://docs.netlify.com/routing/redirects/).

### Sidebar files

The sidebar files define the navigation structure of the documentation pages.

- **Documentation**: [`website/docs/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/docs/sidebar.mjs)
- **Integrations**: [`website/integrations/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/sidebar.mjs)
    - Automatically generated from the categories in [`/website/integrations/categories.mjs`](https://github.com/goauthentik/authentik/blob/main/website/integrations/categories.mjs).
- **API Reference**: [`website/api/sidebar.mjs`](https://github.com/goauthentik/authentik/blob/main/website/api/sidebar.mjs)
    - Mostly automatically generated from authentik API schema.

### Redirects

Sometimes we need to move pages or change URLs. Instead of breaking bookmarks and links, we can define a redirect to automatically send readers from old URLs to new ones.

All our redirects are defined within three files:

- **Documentation**: [`website/docs/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/docs/static/_redirects)
- **Integrations**: [`website/integrations/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/integrations/static/_redirects)
- **API Reference**: [`website/api/static/_redirects`](https://github.com/goauthentik/authentik/blob/main/website/api/static/_redirects)

A `_redirects` file contains a list of rules that define how to handle requests, each of which has the following format:

1. The source URL path (i.e the old URL to match against).
2. The destination URL path (i.e. the new URL to redirect to).
3. The HTTP status code to use when redirecting, followed by an exclamation mark (`!`).

For example, if we moved our applications page:

```text title="website/docs/static/_redirects"
# Source URL Path  | Destination URL Path           | Status Code
/core/applications   /add-secure-apps/applications/   302!
```

Anyone visiting the old URL will automatically land on the new page using a combination of Netlify and Docusaurus.

#### Initial page loads (server-side)

When a reader first visits a documentation page or refreshes their browser:

1. Their browser requests the URL from our server (Netlify).
2. Netlify checks if that exact page exists.
3. If not, it checks our `_redirects` file for a matching rule.
4. The server sends back the correct page, or a 404 if no matching rule exists.

#### Navigating between pages (client-side)

When a reader clicks a link to another documentation page:

1. Docusaurus intercepts the click (no server request needed).
2. The URL in the browser's address bar changes.
3. Docusaurus router fetches the new page content without a full reload.

If Docusaurus's router attempts to render a page that does not exist, the `_redirects` file will be used to determine if a redirect rule should be applied, without a server request or a full reload.

Whether the reader is viewing a page for the first time or navigating between pages, this arrangement allows us to have a single source of truth for all URLs, ensuring that each page remains consistently accessible across authentik versions and throughout our three Docusaurus deployments (Topics, Integrations, and API).

### Updating a page's URL

:::danger[Every URL is a promise]

When someone bookmarks a page or shares a link, they expect it to keep working.

**Before changing any URL, ask yourself:**

- [x] Is this move absolutely necessary?
- [x] Could better organization be achieved without moving files?
- [x] Will this help or confuse readers migrating between authentik versions?

Remember, [Cool URIs don't change!](https://www.w3.org/Provider/Style/URI)
:::

Moving a documentation page to a new location requires updating a `sidebar.mjs` and `_redirects` file.

1. Take note of the page's current URL path in the browser's address bar.
2. Move the Markdown file to the new location.
3. Add a new redirect rule to the `_redirects` file in the respective [documentation directory](#redirects).
4. Update the `sidebar.mjs` file in the respective [documentation directory](#redirects).
