import type { allLocales } from "../../../locale-codes.js";

import type { LocaleModule } from "@lit/localize";
import { msg } from "@lit/localize";

export type TargetLocale = (typeof allLocales)[number];

/**
 * A dummy locale module representing the source locale (English).
 *
 * @remarks
 * This is used to satisfy the return type of {@linkcode LocaleLoaderRecord}
 * for the source locale, which does not need to be loaded.
 */
const sourceTargetModule: LocaleModule = {
    templates: {},
};

/**
 * A record mapping locale codes to their respective human-readable labels.
 *
 * @remarks
 * These are thunked functions to allow for localization via `msg()`.
 */
export const LocaleLabelRecord: Record<TargetLocale, () => string> = {
    "cs_CZ": () => msg("Czech"),
    "en": () => msg("English"),
    "de": () => msg("German"),
    "es": () => msg("Spanish"),
    "fr": () => msg("French"),
    "it": () => msg("Italian"),
    "ja": () => msg("Japanese"),
    "ko": () => msg("Korean"),
    "nl": () => msg("Dutch"),
    "pl": () => msg("Polish"),
    "ru": () => msg("Russian"),
    "tr": () => msg("Turkish"),
    "zh_TW": () => msg("Taiwanese Mandarin"),
    "zh-CN": () => msg("Chinese (simplified)"),
    "zh-Hans": () => msg("Chinese (simplified)"),
    "zh-Hant": () => msg("Chinese (traditional)"),
    "pseudo-LOCALE": () => msg("Pseudolocale (for testing)"),
};

/**
 * A tuple representing a locale label and its corresponding code.
 */
export type LocaleOption = [label: string, code: TargetLocale];

/**
 * Format the locale options for use in a user-facing element.
 *
 * @param locales locales argument for locale-sensitive sorting.
 * @param collatorOptions Optional collator options for locale-sensitive sorting.
 * @returns An array of locale options sorted by their labels.
 */
export function formatLocaleOptions(
    locales?: Intl.LocalesArgument,
    collatorOptions?: Intl.CollatorOptions,
): LocaleOption[] {
    const options = Object.entries(LocaleLabelRecord)
        .map(([code, label]) => {
            return [label(), code];
        })
        .sort(([aLabel], [bLabel]) => aLabel.localeCompare(bLabel, locales, collatorOptions));

    return options as LocaleOption[];
}

/**
 * A record mapping locale codes to their respective module loaders.
 *
 * @remarks
 * The `import` statements **must** reference a locale module path,
 * as this is how ESBuild identifies which files to include in the build.
 */
export const LocaleLoaderRecord: Record<TargetLocale, () => Promise<LocaleModule>> = {
    "cs_CZ": () => import("#locales/cs_CZ"),
    "de": () => import("#locales/de"),
    "en": () => Promise.resolve(sourceTargetModule),
    "es": () => import("#locales/es"),
    "fr": () => import("#locales/fr"),
    "it": () => import("#locales/it"),
    "ja": () => import("#locales/ja"),
    "ko": () => import("#locales/ko"),
    "nl": () => import("#locales/nl"),
    "pl": () => import("#locales/pl"),
    "ru": () => import("#locales/ru"),
    "tr": () => import("#locales/tr"),
    "zh_TW": () => import("#locales/zh_TW"),
    "zh-CN": () => import("#locales/zh-Hans"),
    "zh-Hans": () => import("#locales/zh-Hans"),
    "zh-Hant": () => import("#locales/zh-Hant"),
    "pseudo-LOCALE": () => import("#locales/pseudo-LOCALE"),
};

/**
 * A record mapping locale codes to their respective regex patterns.
 *
 * @remarks
 * While this isn't too useful on its own, we use it to build the {@linkcode LocalePatternCodeMap}
 * while ensuring that TypeScript can verify that all locale codes are covered.
 *
 * The matchers try to conform loosely to [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.txt),
 * "Tags for the Identification of Languages."
 * In practice, language tags have been seen using both hyphens and underscores.
 *
 * Chinese locales usually (but not always) use the script rather than region suffix.
 * The default (optional) fallback for Chinese (zh) is "Chinese (simplified)",
 * which is why it has that odd regex syntax at the end which means "match zh
 * as long as it's not followed by a [:word:] token".
 *
 * Traditional script and the Taiwanese are attempted first, and if neither matches,
 * anything beginning with that generic "zh" is mapped to "Chinese (simplified)."
 */
export const LocalePatternRecord: Record<TargetLocale, RegExp> = {
    "cs_CZ": /^cs([_-]|$)/i,
    "de": /^de([_-]|$)/i,
    "en": /^en([_-]|$)/i,
    "es": /^es([_-]|$)/i,
    "fr": /^fr([_-]|$)/i,
    "it": /^it([_-]|$)/i,
    "ja": /^ja([_-]|$)/i,
    "ko": /^ko([_-]|$)/i,
    "nl": /^nl([_-]|$)/i,
    "pl": /^pl([_-]|$)/i,
    "ru": /^ru([_-]|$)/i,
    "tr": /^tr([_-]|$)/i,
    "zh_TW": /^zh[_-]TW$/i,
    "zh-Hans": /^zh(\b|_)/i,
    "zh-Hant": /^zh[_-](HK|Hant)/i,
    "zh-CN": /^zh(\b|_)/i,
    "pseudo-LOCALE": /^pseudo/i,
};

/**
 * A mapping of regex patterns to locale codes for matching user-supplied locale strings.
 *
 * @see {@linkcode LocalePatternRecord} for the source of this map.
 */
export const LocalePatternCodeMap = new Map<RegExp, TargetLocale>(
    Object.entries(LocalePatternRecord).map(([code, pattern]) => [pattern, code as TargetLocale]),
);
