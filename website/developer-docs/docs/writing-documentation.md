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

## General guidelines

-   The product name authentik should always be stylized as `authentik` (with a lower-case "a" and ending with a "k").
-   Documentation should use American English.
-   You can use standard [Docusaurus-specific features](https://docusaurus.io/docs/next/markdown-features), which include MDX elements such as tabs and admonitions.
-   Use abbreviations where it makes sense (for commonly used terms like SAML and OAuth) for common terms. If an abbreciation is less-known, spell it out in parentheses after the first use.
-   Phrasing should almost always be in present tense and active voice:

    -   DON'T: "The Applications page will be loaded."

    -   DO: "The Applications page displays."

-   Phrasing should never blame the user, and should be subjective:

    -   DON'T: "Never modify the default file."

    -   DO: "We recommend not modifying the default file."

-   When referring to UI text or UI components in authentik, use **bold** text.
-   When referring to other objects in authentik code or functionality, use _cursive_ text, and link to the corresponding documentation if possible.
-   When referring to external tools, give an example how to use the tools or explain how the user can use them.
-   Make sure to add the documentation to the sidebar, if adding a new page.
-   Test how the documentation renders using the Netlify Deploy Preview, especially when using Docusaurus-specific features. Or build it locally and test, using the `make website-watch` command.

If you find any documentation that doesn't match these guidelines, feel free to either open an [Issue](https://github.com/goauthentik/authentik/issues) or a [PR](https://github.com/goauthentik/authentik/pulls) so they can be fixed.

## Integration guidelines

These guidelines apply in addition to the ones above.

See the template in `/website/integrations/_template/service.md`.

-   For placeholders, use angle brackets and italicize the text inside the brackets, to indicate that it is a variable (`_<placeholder-name>_`).

    Make sure to also define if the placeholder is something the user needs to define, is something another system defines, or is randomly generated.

    If you're adding configuration snippets to the documentation, and the snippet is in a language that supports comments, other placeholders may be used, for example comments referencing an earlier step.

-   For placeholder domains, use `authentik.company` and `app-name.company`, where `app-name` is the name of the application that you are writing documentation for.
-   Try to order the documentation in the order that makes it easiest for the user to configure.

-   Make sure to add the service to a fitting category in `/website/sidebarsIntegrations.js`
