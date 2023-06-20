import { sourceLocale, targetLocales } from "@goauthentik/app/locale-codes";

import { configureLocalization } from "@lit/localize";

import { getBestMatchLocale } from "./helpers";

type LocaleGetter = ReturnType<typeof configureLocalization>["getLocale"];
type LocaleSetter = ReturnType<typeof configureLocalization>["setLocale"];

// Internal use only.
//
// This is where the lit-localization module is initialized with our loader, which associates our
// collection of locales with its getter and setter functions.

export function initializeLocalization(): [LocaleGetter, LocaleSetter] {
    const { getLocale, setLocale } = configureLocalization({
        sourceLocale,
        targetLocales,
        loadLocale: async (locale: string) => {
            const localeDef = getBestMatchLocale(locale);
            if (!localeDef) {
                console.warn(`Unrecognized locale: ${localeDef}`);
                return Promise.reject("");
            }
            return localeDef.locale();
        },
    });
    return [getLocale, setLocale];
}

export default initializeLocalization;
export type { LocaleGetter, LocaleSetter };
