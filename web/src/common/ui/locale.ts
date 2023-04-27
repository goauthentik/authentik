import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { messages as enLocale } from "@goauthentik/locales/en";

import { Messages, i18n } from "@lingui/core";
import { fromNavigator, fromUrl } from "@lingui/detect-locale";
import { t } from "@lingui/macro";

interface Locale {
    locale: Messages;
}

export const LOCALES: {
    code: string;
    label: string;
    locale: () => Promise<Locale>;
}[] = [
    {
        code: "en",
        label: t`English`,
        locale: async () => {
            return {
                locale: enLocale,
            };
        },
    },
    {
        code: "debug",
        label: t`Debug`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/pseudo-LOCALE")).messages,
            };
        },
    },
    {
        code: "fr",
        label: t`French`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/fr_FR")).messages,
            };
        },
    },
    {
        code: "tr",
        label: t`Turkish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/tr")).messages,
            };
        },
    },
    {
        code: "es",
        label: t`Spanish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/es")).messages,
            };
        },
    },
    {
        code: "pl",
        label: t`Polish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/pl")).messages,
            };
        },
    },
    {
        code: "zh_TW",
        label: t`Taiwanese Mandarin`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh_TW")).messages,
            };
        },
    },
    {
        code: "zh-CN",
        label: t`Chinese (simplified)`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh-Hans")).messages,
            };
        },
    },
    {
        code: "zh-HK",
        label: t`Chinese (traditional)`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh-Hant")).messages,
            };
        },
    },
    {
        code: "de",
        label: t`German`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/de")).messages,
            };
        },
    },
];

const DEFAULT_FALLBACK = () => "en";

export function autoDetectLanguage() {
    // Always load en locale at the start so we have something and don't error
    i18n.load("en", enLocale);
    i18n.activate("en");

    const locales: string[] = [];
    // Get all locales we can, in order
    // - Global authentik settings (contains user settings)
    // - URL parameter
    // - Navigator
    // - Fallback (en)
    // Remove any invalid values, add broader locales (fr-FR becomes fr)
    // Remove any duplicate values
    [globalAK()?.locale || "", fromUrl("locale"), fromNavigator(), DEFAULT_FALLBACK()]
        .filter((v) => v && v !== "")
        .map((locale) => {
            locales.push(locale);
            // For now we only care about the first locale part
            if (locale.includes("_")) {
                locales.push(locale.split("_")[0]);
            }
            if (locale.includes("-")) {
                locales.push(locale.split("-")[0]);
            }
        })
        .filter((v, idx, arr) => {
            return arr.indexOf(v) === idx;
        });
    console.debug(`authentik/local: Locales to try: ${locales}`);
    for (const tryLocale of locales) {
        if (LOCALES.find((locale) => locale.code === tryLocale)) {
            console.debug(`authentik/locale: Activating detected locale '${tryLocale}'`);
            activateLocale(tryLocale);
            return;
        } else {
            console.debug(`authentik/locale: No matching locale for ${tryLocale}`);
        }
    }
    console.debug(`authentik/locale: No locale for '${locales}', falling back to en`);
    activateLocale(DEFAULT_FALLBACK());
}

export function activateLocale(code: string) {
    const urlLocale = fromUrl("locale");
    if (urlLocale !== null && urlLocale !== "") {
        code = urlLocale;
    }
    const locale = LOCALES.find((locale) => locale.code == code);
    if (!locale) {
        console.warn(`authentik/locale: failed to find locale for code ${code}`);
        return;
    }
    locale.locale().then((localeData) => {
        console.debug(`authentik/locale: Loaded locale '${code}'`);
        if (i18n.locale === code) {
            return;
        }
        i18n.load(locale.code, localeData.locale);
        i18n.activate(locale.code);
        window.dispatchEvent(
            new CustomEvent(EVENT_LOCALE_CHANGE, {
                bubbles: true,
                composed: true,
            }),
        );
    });
}
