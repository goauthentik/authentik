import { formatter } from "@lingui/format-po-gettext";

export default {
    sourceLocale: "en",
    locales: [
        "en",
        "pseudo-LOCALE",
        "fr_FR",
        "tr",
        "es",
        "pl",
        "zh_TW",
        "zh-Hans",
        "zh-Hant",
        "de",
    ],
    pseudoLocale: "pseudo-LOCALE",
    fallbackLocales: {
        "pseudo-LOCALE": "en",
        "default": "en",
    },
    compileNamespace: "ts",
    catalogs: [
        {
            path: "src/locales/{locale}",
            include: ["src"],
            exclude: ["**/node_modules/**", "**/dist/**"],
        },
    ],
    format: formatter({ lineNumbers: false }),
};
