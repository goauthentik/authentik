import { globalAK } from "@goauthentik/common/global";
import { sourceLocale, targetLocales } from "@goauthentik/locales/generated/index";

import { LocaleModule, configureLocalization, msg } from "@lit/localize";

export const FALLBACK_LOCALE = {
    code: "en",
    label: msg("English"),
    locale: async () => {
        return await import("@goauthentik/locales/generated/en");
    },
};

export const LOCALES: {
    code: string;
    label: string;
    locale: () => Promise<LocaleModule>;
}[] = [
    FALLBACK_LOCALE,
    {
        code: "fr",
        label: msg("French"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/fr_FR");
        },
    },
    {
        code: "tr",
        label: msg("Turkish"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/tr");
        },
    },
    {
        code: "es",
        label: msg("Spanish"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/es");
        },
    },
    {
        code: "pl",
        label: msg("Polish"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/pl");
        },
    },
    {
        code: "zh_TW",
        label: msg("Taiwanese Mandarin"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/zh_TW");
        },
    },
    {
        code: "zh-CN",
        label: msg("Chinese (simplified)"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/zh-Hans");
        },
    },
    {
        code: "zh-HK",
        label: msg("Chinese (traditional)"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/zh-Hant");
        },
    },
    {
        code: "de",
        label: msg("German"),
        locale: async () => {
            return await import("@goauthentik/locales/generated/de");
        },
    },
];

export const { getLocale, setLocale } = configureLocalization({
    sourceLocale,
    targetLocales,
    loadLocale: async (code: string) => {
        let locale = LOCALES.find((locale) => locale.code === code);
        if (!locale) {
            locale = FALLBACK_LOCALE;
        }
        return await locale?.locale();
    },
});

export function autoDetectLanguage() {
    const detected = [globalAK()?.locale, ...navigator.languages, "en"].filter((l) => l);
    detected.map((locale) => {
        if (!locale) return;
        // For now we only care about the first locale part
        if (locale.includes("_")) {
            detected.push(locale.split("_")[0]);
        }
        if (locale.includes("-")) {
            detected.push(locale.split("-")[0]);
        }
    });
    for (const tryLocale of detected) {
        if (LOCALES.find((locale) => locale.code === tryLocale)) {
            console.debug(`authentik/locale: Activating detected locale '${tryLocale}'`);
            setLocale(tryLocale as string);
            return;
        } else {
            console.debug(`authentik/locale: No matching locale for ${tryLocale}`);
        }
    }
    console.debug(`authentik/locale: No locale for '${detected}', falling back to en`);
    setLocale("en");
}
