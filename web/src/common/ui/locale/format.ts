import { allLocales } from "../../../locale-codes.js";

import { CJKLanguageTag, isCJKLanguageTag, isHanLanguageTag } from "#common/ui/locale/cjk";
import {
    PseudoLanguageTag,
    SourceLanguageTag,
    TargetLanguageTag,
} from "#common/ui/locale/definitions";
import { safeParseLocale } from "#common/ui/locale/utils";

import { msg, str } from "@lit/localize";

/**
 * Safely get a minimized locale ID, with fallback for older browsers.
 */
function getMinimizedLocaleID(tag: string): string {
    const locale = safeParseLocale(tag);
    if (!locale) {
        return tag.split(/[-_]/)[0].toLowerCase();
    }

    try {
        return locale.minimize().baseName;
    } catch {
        return locale.language;
    }
}

/**
 * Get the appropriate locale ID for display purposes.
 * Han scripts use full baseName; others use just the language.
 */
function getDisplayLocaleID(tag: TargetLanguageTag): string {
    const locale = safeParseLocale(tag);
    if (!locale) {
        return tag;
    }

    if (isHanLanguageTag(tag)) {
        return locale.baseName;
    }

    return locale.language;
}

export function formatDisplayName(
    localeID: Intl.Locale | Intl.UnicodeBCP47LocaleIdentifier,
    fallback?: string,
    languageNames?: Intl.DisplayNames,
): string {
    const id = typeof localeID === "string" ? localeID : localeID.baseName;
    fallback ??= id;

    languageNames ??= new Intl.DisplayNames([id], {
        type: "language",
    });

    try {
        return languageNames.of(id) || fallback;
    } catch {
        return fallback;
    }
}

/**
 * Given a localized display name, normalize it for comparison or sorting,
 * removing diacritics and other marks.
 */
export function normalizeDisplayName(displayName: string): string {
    return displayName
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

/**
 * A triple representing a locale and its corresponding display names.
 */
export type LocaleDisplay = [
    locale: TargetLanguageTag,
    localizedDisplayName: string,
    relativeDisplayName: string,
];

export function createIntlCollator(
    activeLocale: Intl.UnicodeBCP47LocaleIdentifier,
    options: Intl.CollatorOptions,
) {
    const activeIsCJK = isCJKLanguageTag(activeLocale);

    return ([aLocale, aName]: LocaleDisplay, [bLocale, bName]: LocaleDisplay) => {
        // Active locale always first
        if (activeLocale === aLocale) return -1;
        if (activeLocale === bLocale) return 1;

        // Pseudo locale always last
        if (PseudoLanguageTag === aLocale) return 1;
        if (PseudoLanguageTag === bLocale) return -1;

        const aIsCJK = isCJKLanguageTag(aLocale);
        const bIsCJK = isCJKLanguageTag(bLocale);

        // Group CJK languages together
        if (aIsCJK !== bIsCJK) {
            return aIsCJK ? (activeIsCJK ? -1 : 1) : activeIsCJK ? 1 : -1;
        }

        // Within CJK: group Han scripts together
        if (aIsCJK && bIsCJK) {
            const aIsHan = isHanLanguageTag(aLocale);
            const bIsHan = isHanLanguageTag(bLocale);

            if (aIsHan !== bIsHan) {
                return aIsHan ? -1 : 1;
            }
        }

        return aName.localeCompare(bName, activeLocale, options);
    };
}

export interface FormatLocaleOptionsInit {
    languageNames?: Intl.DisplayNames;
    collatorOptions?: Intl.CollatorOptions;
    debug?: boolean;
}

/**
 * Pre-defined display names for locales that need special handling.
 * These use minimized IDs or explicit fallbacks.
 */
const SPECIAL_LOCALE_FALLBACKS: ReadonlyMap<TargetLanguageTag, () => string> = new Map([
    [SourceLanguageTag, () => msg("English", { id: "en" })],
    [CJKLanguageTag.HanSimplified, () => msg("Chinese (Simplified)", { id: "zh-Hans" })],
    [CJKLanguageTag.HanTraditional, () => msg("Chinese (Traditional)", { id: "zh-Hant" })],
    [CJKLanguageTag.Japanese, () => msg("Japanese", { id: "ja-JP" })],
    [CJKLanguageTag.Korean, () => msg("Korean", { id: "ko-KR" })],
    [PseudoLanguageTag, () => msg("English (Pseudo-Accents)", { id: "en-XA" })],
]);

/**
 * Format the locale options for use in a user-facing element.
 *
 * @returns An array of locale options sorted by their labels.
 */
export function formatLocaleDisplayNames(
    activeLanguageTag: Intl.UnicodeBCP47LocaleIdentifier | Intl.Locale,
    { collatorOptions = {}, languageNames, debug }: FormatLocaleOptionsInit = {},
): LocaleDisplay[] {
    const activeLocaleTag =
        typeof activeLanguageTag === "string" ? activeLanguageTag : activeLanguageTag.baseName;

    languageNames ??= new Intl.DisplayNames(activeLocaleTag, {
        type: "language",
    });

    const usedLanguages = new Set<string>();
    const displayNames = new Map<TargetLanguageTag, string>();

    // Process all locales
    for (const tag of allLocales) {
        // Skip pseudo unless debug
        if (tag === PseudoLanguageTag && !debug) {
            continue;
        }

        const specialFallback = SPECIAL_LOCALE_FALLBACKS.get(tag);

        if (specialFallback) {
            const localeID = isHanLanguageTag(tag)
                ? tag // Prefer the display name over region minimization.
                : getMinimizedLocaleID(tag);

            displayNames.set(tag, formatDisplayName(localeID, specialFallback(), languageNames));
        } else {
            // Standard locales: prefer language-only if not already used
            const locale = safeParseLocale(tag);
            const language = locale?.language ?? tag.split(/[-_]/)[0].toLowerCase();

            const localeID = usedLanguages.has(language) ? (locale?.baseName ?? tag) : language;

            usedLanguages.add(language);
            displayNames.set(tag, formatDisplayName(localeID, language, languageNames));
        }
    }

    // Build display entries with relative names
    const entries: LocaleDisplay[] = Array.from(displayNames, ([tag, localizedName]) => {
        const relativeLanguageNames = new Intl.DisplayNames(tag, { type: "language" });
        const localeID = getDisplayLocaleID(tag);
        const relativeName = formatDisplayName(localeID, localizedName, relativeLanguageNames);

        return [tag, localizedName, relativeName];
    });

    return entries.sort(createIntlCollator(activeLocaleTag, collatorOptions));
}

export function formatRelativeLocaleDisplayName(
    languageTag: TargetLanguageTag,
    localizedDisplayName: string,
    relativeDisplayName: string,
) {
    const pseudo = languageTag === PseudoLanguageTag;

    const same =
        relativeDisplayName &&
        normalizeDisplayName(relativeDisplayName) === normalizeDisplayName(localizedDisplayName);

    if (same || pseudo) {
        return localizedDisplayName;
    }

    return msg(str`${relativeDisplayName} (${localizedDisplayName})`, {
        id: "locale-option-localized-label",
        desc: "Locale option label showing the localized language name along with the native language name in parentheses.",
    });
}

/**
 * Format the display name for the auto-detect locale option.
 *
 * @param detectedLocale The detected locale display, if any.
 */
export function formatAutoDetectLocaleDisplayName(detectedLocale?: LocaleDisplay | null) {
    const prefix = msg("Auto-detect", {
        id: "locale-auto-detect-option",
        desc: "Label for the auto-detect locale option in language selection dropdown",
    });

    if (!detectedLocale) {
        return prefix;
    }

    return `${prefix} (${formatRelativeLocaleDisplayName(...detectedLocale)})`;
}
