import { EVENT_LOCALE_CHANGE } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import * as enLocale from "@goauthentik/locales/en";

import { configureLocalization } from "@lit/localize";
import { msg } from "@lit/localize";

// Generated via output.localeCodesModule
import { sourceLocale, targetLocales } from "../../locale-codes";

interface Locale {
    locale: Messages;
}

export type AkLocale = {
    code: string;
    label: string;
    locale: () => Promise<Locale>;
};

export const LOCALES: AkLocale[] = [
    {
        code: "en",
        label: msg("English"),
        locale: async () => enLocale,
    },
    {
        code: "debug",
        label: msg("Debug"),
        locale: async () => await import("@goauthentik/locales/pseudo-LOCALE"),
    },
    {
        code: "fr",
        label: msg("French"),
        locale: async () => await import("@goauthentik/locales/fr_FR"),
    },
    {
        code: "tr",
        label: msg("Turkish"),
        locale: async () => await import("@goauthentik/locales/tr"),
    },
    {
        code: "es",
        label: msg("Spanish"),
        locale: async () => await import("@goauthentik/locales/es"),
    },
    {
        code: "pl",
        label: msg("Polish"),
        locale: async () => await import("@goauthentik/locales/pl"),
    },
    {
        code: "zh_TW",
        label: msg("Taiwanese Mandarin"),
        locale: async () => await import("@goauthentik/locales/zh_TW"),
    },
    {
        code: "zh-CN",
        label: msg("Chinese (simplified)"),
        locale: async () => await import("@goauthentik/locales/zh-Hans"),
    },
    {
        code: "zh-HK",
        label: msg("Chinese (traditional)"),
        locale: async () => await import("@goauthentik/locales/zh-Hant"),
    },
    {
        code: "de",
        label: msg("German"),
        locale: async () => await import("@goauthentik/locales/de"),
    },
];

export const { getLocale, setLocale } = configureLocalization({
    sourceLocale,
    targetLocales,
    loadLocale: async (locale) => {
        const localeDef = LOCALES.find((l) => l.code === locale);
        if (!localeDef) {
            console.warn(`Unrecognized locale: ${localeDef}`);
            return Promise.reject("");
        }
        return localeDef.locale();
    },
});

const DEFAULT_FALLBACK = "en";

export const fromUrl = (param = "locale") => {
    const url = new URL(window.location.href);
    return url.searchParams.get(param) || "";
};

export function autoDetectLanguage() {
    // Always load en locale at the start so we have something and don't error
    setLocale("en");

    // Get all locales we can, in order
    // - Global authentik settings (contains user settings)
    // - URL parameter
    // - Navigator
    // - Fallback (en)

    const localeCandidates = [
        globalAK()?.locale || "",
        fromUrl("locale"),
        window.navigator.language ?? "",
        DEFAULT_FALLBACK,
    ];

    // Remove any invalid values, add broader locales (fr-FR becomes fr)
    // Remove any duplicate values

    // https://mail.mozilla.org/pipermail/es-discuss/2012-February/020525.html
    // Sets are order-preserving to ensure reproducibility of test results and
    // eliminate the side-channel attacks that come from irreproducibility.

    // prettier-ignore
    const requestedLocales = Array.from(
        new Set(localeCandidates
            .filter((v) => v && v !== "")
            .reduce((locales: string[], locale: string) => {
                const localePrefix = locale.split(/[_-]/)[0];
                return localePrefix === locale ? [...locales, locale] : [...locales, locale, localePrefix];
            }, [])));

    function localeInLibrary(tryLocale: string) {
        const found = LOCALES.find((l) => l.code === tryLocale);
        if (!found) {
            console.debug(`authentik/locale: No matching entry for requested locale ${tryLocale}`);
        }
        return found;
    }

    const firstSupportedLocale = requestedLocales.find(localeInLibrary);

    if (!firstSupportedLocale) {
        console.debug(`authentik/locale: No locale for '${locales}', falling back to en`);
        activateLocale(DEFAULT_FALLBACK());
        return;
    }

    activateLocale(firstSupportedLocale);
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
        if (getLocale() === code) {
            return;
        }

        console.log(`Setting Locale to ... ${locale.label} (${locale.code})`);
        setLocale(locale.code);
        window.dispatchEvent(
            new CustomEvent(EVENT_LOCALE_CHANGE, {
                bubbles: true,
                composed: true,
            })
        );
    });
}
