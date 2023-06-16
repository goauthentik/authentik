import { LOCALES as RAW_LOCALES, enLocale } from "./definitions";
import { AkLocale } from "./types";

// NOTE: This is the definition of the LOCALES table that most of the code uses. The 'definitions'
// file is relatively pure, but here we establish that we want the English locale to loaded when an
// application is first instantiated.

export const LOCALES = RAW_LOCALES.map((locale) =>
    locale.code === "en" ? { ...locale, locale: async () => enLocale } : locale,
);

// First attempt a precise match, then see if there's a precise match on the requested locale's
// prefix, then find the *first* locale for which that locale's prefix matches the requested prefix.

export function getBestMatchLocale(locale: string): AkLocale | undefined {
    return LOCALES.find((l) => l.match.test(locale));
}

// This looks weird, but it's sensible: we have several candidates, and we want to find the first
// one that has a supported locale. Then, from *that*, we have to extract that first supported
// locale.

export function findSupportedLocale(candidates: string[]) {
    const candidate = candidates.find((candidate: string) => getBestMatchLocale(candidate));
    return candidate ? getBestMatchLocale(candidate) : undefined;
}

export function localeFromUrl(param = "locale") {
    const url = new URL(window.location.href);
    return url.searchParams.get(param) || "";
}
