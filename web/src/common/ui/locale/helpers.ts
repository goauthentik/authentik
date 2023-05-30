import * as enLocale from "@goauthentik/locales/en";

import { LOCALES as RAW_LOCALES } from "./definitions";

// NOTE: This is the definition of the LOCALES table that most of the code uses. The 'definitions'
// file is relatively pure, but here we establish that we want the English locale to loaded when an
// application is first instantiated.

export const LOCALES = RAW_LOCALES.map((locale) =>
    locale.code === "en" ? { ...locale, locale: async () => enLocale } : locale
);

// First attempt a precise match, then see if there's a precise match on the requested locale's
// prefix, then find the *first* locale for which that locale's prefix matches the requested prefix.

export function getBestMatchLocale(locale: string) {
    const getPref = (l: string) => l.split(/[_-]/)[0];
    const altLocale = getPref(locale);

    return (
        LOCALES.find((l) => l.code === locale) ||
        LOCALES.find((l) => l.code === altLocale) ||
        LOCALES.find((l) => getPref(l.code) === altLocale)
    );
}

export function findSupportedLocale(candidates: string[]) {
    const candidate = candidates.find((candidate: string) => getBestMatchLocale(candidate));
    return getBestMatchLocale(candidate);
}

export function localeFromUrl(param = "locale") {
    const url = new URL(window.location.href);
    return url.searchParams.get(param) || "";
}
