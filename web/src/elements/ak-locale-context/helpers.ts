import { globalAK } from "@goauthentik/common/global";

import { AKLocalDefinitions } from "./definitions.js";
import { AKLocaleDefinition } from "./types.js";

export const DEFAULT_LOCALE = "en";

export const EVENT_REQUEST_LOCALE = "ak-request-locale";

/**
 * Find the locale definition for a given language code.
 */
export function findLocaleDefinition(languageCode: string): AKLocaleDefinition | null {
    for (const locale of AKLocalDefinitions) {
        if (locale.pattern.test(languageCode)) {
            return locale;
        }
    }

    return null;
}

// This looks weird, but it's sensible: we have several candidates, and we want to find the first
// one that has a supported locale. Then, from *that*, we have to extract that first supported
// locale.

export function findSupportedLocale(candidates: string[]): AKLocaleDefinition | null {
    for (const candidate of candidates) {
        const locale = findLocaleDefinition(candidate);

        if (locale) return locale;
    }

    return null;
}

export function localeCodeFromURL(param = "locale") {
    const searchParams = new URLSearchParams(window.location.search);

    return searchParams.get(param);
}

function isLocaleCodeCandidate(input: unknown): input is string {
    if (typeof input !== "string") return false;

    return !!input;
}

/**
 * Auto-detect the most appropriate locale.
 *
 * @remarks
 *
 * The order of precedence is:
 *
 * 1. URL parameter `locale`.
 * 2. User's preferred locale, if any.
 * 3. Browser's preferred locale, if any.
 * 4. Brand's preferred locale, if any.
 * 5. Default locale.
 *
 * @param requestedLanguageCode - The user's preferred locale, if any.
 * @param brandLanguageCode - The brand's preferred locale, if any.
 *
 * @returns The most appropriate locale.
 */
export function autoDetectLanguage(
    requestedLanguageCode?: string,
    brandLanguageCode?: string,
): string {
    const localeCandidates = [
        localeCodeFromURL("locale"),
        requestedLanguageCode,
        window.navigator?.language,
        brandLanguageCode,
        globalAK()?.locale,
    ].filter(isLocaleCodeCandidate);

    const firstSupportedLocale = findSupportedLocale(localeCandidates);

    if (!firstSupportedLocale) {
        console.debug(
            `authentik/locale: No locale found for '[${localeCandidates}.join(',')]', falling back to ${DEFAULT_LOCALE}`,
        );

        return DEFAULT_LOCALE;
    }

    return firstSupportedLocale.languageCode;
}

export default autoDetectLanguage;
