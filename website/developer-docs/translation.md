---
title: Translations
---

Translation in authentik is done in two places. Most of the text is defined in the frontend in `web/`, and a subset of messages is defined in the backend.

The frontend uses [lingui](https://lingui.js.org/), and the backend uses the built-in django translation tools.

:::info
Please review the [Writing documentation](./docs/writing-documentation) guidelines as they apply to documentation too.
:::

## Online translation

To simplify translation you can use https://www.transifex.com/beryjuorg/authentik/, which has no local requirements.

## Local translation

### Prerequisites

-   Node (any recent version should work, we use 16.x to build)
-   Make (again, any recent version should work)
-   Docker

Run `npm i` in the `/web` folder to install all dependencies.

Ensure the language code is in the `package.json` file in `web/`:

```json
    // [...]
    "lingui": {
        // [...]
        "locales": [
            "en",
            "pseudo-LOCALE",
            "a-new-locale"
        ],
    // [...]
```

Afterwards, run `npx lingui extract` to generate a base .po file.

The .po files can be edited by any text editor, or using a tool such as [POEdit](https://poedit.net/).

To see the change, run `npm run watch` in the `web/` directory.
