---
title: Translations
---

Translation in authentik is done in two places. Most of the text is defined in the frontend in `web/`, and a subset of messages is defined in the backend.

The frontend uses [@lit/localize](https://lit.dev/docs/localization/overview/), and the backend uses the built-in django translation tools.

:::info
Please review the [Writing documentation](./docs/writing-documentation) guidelines as they apply to documentation too.
:::

## Online translation

To simplify translation you can use https://www.transifex.com/authentik/authentik, which has no local requirements.

## Local translation

### Prerequisites

-   Node (any recent version should work, we use 16.x to build)
-   Make (again, any recent version should work)
-   Docker

Run `npm i` in the `/web` folder to install all dependencies.

Ensure the language code is in the `lit-localize.json` file in `web/`:

```json
    // [...]
    "targetLocales": [
        "en",
        "pseudo-LOCALE",
        "a-new-locale"
        // [...]
    ],
    // [...]
```

Afterwards, run `make web-i18n-extract` to generate a base .xlf file.

The .xlf files can be edited by any text editor, or using a tool such as [POEdit](https://poedit.net/).

To see the change, run `make web-watch` in the root directory of the repository.
