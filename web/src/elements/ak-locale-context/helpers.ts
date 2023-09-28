import { globalAK } from "@goauthentik/common/global";

import { LOCALES as RAW_LOCALES, enLocale } from "./definitions";
import { AkLocale } from "./types";

export const DEFAULT_LOCALE = "en";

export const EVENT_REQUEST_LOCALE = "ak-request-locale";

const TOMBSTONE = "⛼⛼tombstone⛼⛼";

// NOTE: This is the definition of the LOCALES table that most of the code uses. The 'definitions'
// file is relatively pure, but here we establish that we want the English locale to loaded when an
// application is first instantiated.

export const LOCALES = RAW_LOCALES.map((locale) =>
    locale.code === "en" ? { ...locale, locale: async () => enLocale } : locale,
);

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

export function localeCodeFromUrl(param = "locale") {
    const url = new URL(window.location.href);
    return url.searchParams.get(param) || "";
}

// Get all locales we can, in order
// - Global authentik settings (contains user settings)
// - URL parameter
// - A requested code passed in, if any
// - Navigator
// - Fallback (en)

const isLocaleCandidate = (v: unknown): v is string =>
    typeof v === "string" && v !== "" && v !== TOMBSTONE;

export function autoDetectLanguage(requestedCode?: string): string {
    const localeCandidates: string[] = [
        globalAK()?.locale ?? TOMBSTONE,
        localeCodeFromUrl("locale"),
        requestedCode ?? TOMBSTONE,
        window.navigator?.language ?? TOMBSTONE,
        DEFAULT_LOCALE,
    ].filter(isLocaleCandidate);

    const firstSupportedLocale = findSupportedLocale(localeCandidates);

    if (!firstSupportedLocale) {
        console.debug(
            `authentik/locale: No locale found for '[${localeCandidates}.join(',')]', falling back to ${DEFAULT_LOCALE}`,
        );
        return DEFAULT_LOCALE;
    }

    return firstSupportedLocale.code;
}

export default autoDetectLanguage;
