import { sourceLocale } from "../../../locale-codes.js";

import { LocalePatternCodeMap, TargetLocale } from "#common/ui/locale/definitions";

export function getBestMatchLocale(locale: string): TargetLocale | null {
    const [, localeCode] =
        Iterator.from(LocalePatternCodeMap).find(([pattern]) => pattern.test(locale)) || [];

    return localeCode ?? null;
}

/**
 * Find the first supported locale from a list of candidates.
 *
 * @param candidates An array of locale strings to check.
 * @returns The first supported locale code, or null if none found.
 *
 * @remarks
 * This looks weird, but it's sensible: we have several candidates, and we want to find the first
 * one that has a supported locale. Then, from *that*, we have to extract that first supported
 * locale.
 */
export function findSupportedLocale(candidates: string[]): TargetLocale | null {
    const candidate = candidates.find((candidate) => getBestMatchLocale(candidate));
    return candidate ? getBestMatchLocale(candidate) : null;
}

const sessionLocaleKey = "authentik:locale";

/**
 * Persist the given locale code to sessionStorage.
 */
export function setSessionLocale(locale: TargetLocale | null): void {
    try {
        if (!locale || locale === sourceLocale) {
            sessionStorage?.removeItem?.(sessionLocaleKey);
            return;
        }

        sessionStorage?.setItem?.(sessionLocaleKey, locale);
    } catch (error) {
        console.debug("authentik/locale: Unable to persist locale to sessionStorage", error);
    }
}

/**
 * Retrieve the persisted locale code from sessionStorage.
 */
export function getSessionLocale(): string | null {
    try {
        return sessionStorage?.getItem?.(sessionLocaleKey) || null;
    } catch (error) {
        console.debug("authentik/locale: Unable to read locale from sessionStorage", error);
    }

    return null;
}

/**
 * Auto-detect the best locale to use from several sources.
 *
 * @param localeHint An optional locale code hint.
 * @param fallbackLocaleCode An optional fallback locale code.
 * @returns The best-matching supported locale code.
 *
 * @remarks
 * The order of precedence is:
 *
 * 1. A `locale` URL parameter
 * 2. A previously persisted session locale
 * 3. A provided locale hint
 * 4. The browser's navigator language
 * 5. A provided fallback locale code
 * 6. The source locale (English)
 */
export function autoDetectLanguage(localeHint?: string, fallbackLocaleCode?: string): TargetLocale {
    let localeParam: string | null = null;

    if (self.location) {
        const searchParam = new URLSearchParams(self.location.search);

        localeParam = searchParam.get("locale");
    }

    const sessionLocale = getSessionLocale();

    const candidates = [
        sessionLocale,
        localeParam,
        localeHint,
        self.navigator?.language,
        fallbackLocaleCode,
    ].filter((item): item is string => !!item);

    const firstSupportedLocale = findSupportedLocale(candidates);

    if (!firstSupportedLocale) {
        console.debug(`authentik/locale: Falling back to source locale`, {
            sourceLocale,
            localeHint,
            fallbackLocaleCode,
            candidates,
        });

        return sourceLocale;
    }

    return firstSupportedLocale;
}
