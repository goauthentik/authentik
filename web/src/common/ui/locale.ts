import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";

import { Messages, i18n } from "@lingui/core";
import { detect, fromNavigator, fromUrl } from "@lingui/detect-locale";
import { t } from "@lingui/macro";

interface Locale {
    locale: Messages;
    plurals: (n: string | number, ord?: boolean | undefined) => string;
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
                locale: (await import("@goauthentik/locales/en")).messages,
                plurals: (await import("make-plural/plurals")).en,
            };
        },
    },
    {
        code: "debug",
        label: t`Debug`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/pseudo-LOCALE")).messages,
                plurals: (await import("make-plural/plurals")).en,
            };
        },
    },
    {
        code: "fr",
        label: t`French`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/fr_FR")).messages,
                plurals: (await import("make-plural/plurals")).fr,
            };
        },
    },
    {
        code: "tr",
        label: t`Turkish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/tr")).messages,
                plurals: (await import("make-plural/plurals")).tr,
            };
        },
    },
    {
        code: "es",
        label: t`Spanish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/es")).messages,
                plurals: (await import("make-plural/plurals")).es,
            };
        },
    },
    {
        code: "pl",
        label: t`Polish`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/pl")).messages,
                plurals: (await import("make-plural/plurals")).pl,
            };
        },
    },
    {
        code: "zh_TW",
        label: t`Taiwanese Mandarin`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh_TW")).messages,
                plurals: (await import("make-plural/plurals")).zh,
            };
        },
    },
    {
        code: "zh-CN",
        label: t`Chinese (simplified)`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh-Hans")).messages,
                plurals: (await import("make-plural/plurals")).zh,
            };
        },
    },
    {
        code: "zh-HK",
        label: t`Chinese (traditional)`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/zh-Hant")).messages,
                plurals: (await import("make-plural/plurals")).zh,
            };
        },
    },
    {
        code: "de",
        label: t`German`,
        locale: async () => {
            return {
                locale: (await import("@goauthentik/locales/de")).messages,
                plurals: (await import("make-plural/plurals")).de,
            };
        },
    },
];

const DEFAULT_FALLBACK = () => "en";

export function autoDetectLanguage() {
    const detected =
        detect(
            () => {
                return globalAK()?.locale;
            },
            fromUrl("locale"),
            fromNavigator(),
            DEFAULT_FALLBACK,
        ) || DEFAULT_FALLBACK();
    const locales = [detected];
    // For now we only care about the first locale part
    if (detected.includes("_")) {
        locales.push(detected.split("_")[0]);
    }
    if (detected.includes("-")) {
        locales.push(detected.split("-")[0]);
    }
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
        i18n.loadLocaleData(locale.code, { plurals: localeData.plurals });
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
