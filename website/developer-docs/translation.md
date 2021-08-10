---
title: Translation
---

Translation in authentik is done in two places. Most of the text is defined in the frontend in `web/`, and a subset of messages is defined in the backend.

The frontend uses [lingui](https://lingui.js.org/), and the backend uses the built-in django translation tools.

## Frontend

If you want to translate the frontend to a new language, ensure the language code is in the `package.json` file in `web/`:

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

You should have `@lingui/cli` and `@babel/core` installed in your home directory (See [LinguiJS Docs](https://lingui.js.org/tutorials/setup-react.html) for more information).

Afterwards, run `npx lingui extract` to generate a base .po file.

The .po files can be edited by any text editor, or using a tool such as [POEdit](https://poedit.net/).

To see the change, run `npm run watch` in the `web/` directory.
