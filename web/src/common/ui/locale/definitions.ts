import { type allLocales, sourceLocale } from "../../../locale-codes.js";

import type { LocaleModule } from "@lit/localize";
import { msg } from "@lit/localize";

export type TargetLocale = (typeof allLocales)[number];

/**
 * The pseudo locale code.
 */
export const PseudoLocale = "pseudo-LOCALE" satisfies TargetLocale;

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
    [sourceLocale]: () => msg("English"),
    [PseudoLocale]: () => msg("Pseudolocale (for testing)"),
    "cs-CZ": () => msg("Czech"),
    "de-DE": () => msg("German"),
    "es-ES": () => msg("Spanish"),
    "fr-FR": () => msg("French"),
    "it-IT": () => msg("Italian"),
    "ja-JP": () => msg("Japanese"),
    "ko-KR": () => msg("Korean"),
    "nl-NL": () => msg("Dutch"),
    "pl-PL": () => msg("Polish"),
    "ru-RU": () => msg("Russian"),
    "tr-TR": () => msg("Turkish"),
    "zh-Hans": () => msg("Chinese (simplified)"),
    "zh-Hant": () => msg("Chinese (traditional)"),
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
    [sourceLocale]: () => Promise.resolve(sourceTargetModule),
    [PseudoLocale]: () => import("#locales/pseudo-LOCALE"),
    "cs-CZ": () => import("#locales/cs-CZ"),
    "de-DE": () => import("#locales/de-DE"),
    "es-ES": () => import("#locales/es-ES"),
    "fr-FR": () => import("#locales/fr-FR"),
    "it-IT": () => import("#locales/it-IT"),
    "ja-JP": () => import("#locales/ja-JP"),
    "ko-KR": () => import("#locales/ko-KR"),
    "nl-NL": () => import("#locales/nl-NL"),
    "pl-PL": () => import("#locales/pl-PL"),
    "ru-RU": () => import("#locales/ru-RU"),
    "tr-TR": () => import("#locales/tr-TR"),
    "zh-Hans": () => import("#locales/zh-Hans"),
    "zh-Hant": () => import("#locales/zh-Hant"),
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
 * Chinese language (`zh` or _Zhongwen_) can have a subtag indicating script:
 *
 * - `Hans`: Simplified
 * - `Hant`: Traditional
 *
 * Alternatively, the subtag can indicate a region with a predominant script.
 * The fallback is simplified Chinese.
 */
export const LocalePatternRecord: Record<TargetLocale, RegExp> = {
    [sourceLocale]: /^en([_-]|$)/i,
    [PseudoLocale]: /^pseudo/i,
    "cs-CZ": /^cs([_-]|$)/i,
    "de-DE": /^de([_-]|$)/i,
    "es-ES": /^es([_-]|$)/i,
    "fr-FR": /^fr([_-]|$)/i,
    "it-IT": /^it([_-]|$)/i,
    "ja-JP": /^ja([_-]|$)/i,
    "ko-KR": /^ko([_-]|$)/i,
    "nl-NL": /^nl([_-]|$)/i,
    "pl-PL": /^pl([_-]|$)/i,
    "ru-RU": /^ru([_-]|$)/i,
    "tr-TR": /^tr([_-]|$)/i,
    /**
     * Traditional Chinese.
     *
     * The region subtag is required.
     */
    "zh-Hant": /^zh[_-](TW|HK|MO|Hant)/i,
    /**
     * Simplified Chinese.
     *
     * The region subtag is optional.
     */
    "zh-Hans": /^zh([_-](CN|SG|MY|Hans)|$)/i,
};

/**
 * A mapping of regex patterns to locale codes for matching user-supplied locale strings.
 *
 * @see {@linkcode LocalePatternRecord} for the source of this map.
 */
export const LocalePatternCodeMap = new Map<RegExp, TargetLocale>(
    Object.entries(LocalePatternRecord).map(([code, pattern]) => [pattern, code as TargetLocale]),
);
