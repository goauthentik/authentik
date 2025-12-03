import { type allLocales, sourceLocale } from "../../../locale-codes.js";

import type { LocaleModule } from "@lit/localize";
import { msg } from "@lit/localize";

export type TargetLocale = (typeof allLocales)[number];

/**
 * The pseudo locale code.
 */
export const PseudoLocale = "pseudo_LOCALE" satisfies TargetLocale;

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
    pseudo_LOCALE: () => msg("Pseudolocale (for testing)"),
    cs_CZ: () => msg("Czech"),
    de_DE: () => msg("German"),
    es_ES: () => msg("Spanish"),
    fr_FR: () => msg("French"),
    it_IT: () => msg("Italian"),
    ja_JP: () => msg("Japanese"),
    ko_KR: () => msg("Korean"),
    nl_NL: () => msg("Dutch"),
    pl_PL: () => msg("Polish"),
    ru_RU: () => msg("Russian"),
    tr_TR: () => msg("Turkish"),
    zh_Hans: () => msg("Chinese (simplified)"),
    zh_Hant: () => msg("Chinese (traditional)"),
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
    pseudo_LOCALE: () => import("#locales/pseudo_LOCALE"),
    cs_CZ: () => import("#locales/cs_CZ"),
    de_DE: () => import("#locales/de_DE"),
    es_ES: () => import("#locales/es_ES"),
    fr_FR: () => import("#locales/fr_FR"),
    it_IT: () => import("#locales/it_IT"),
    ja_JP: () => import("#locales/ja_JP"),
    ko_KR: () => import("#locales/ko_KR"),
    nl_NL: () => import("#locales/nl_NL"),
    pl_PL: () => import("#locales/pl_PL"),
    ru_RU: () => import("#locales/ru_RU"),
    tr_TR: () => import("#locales/tr_TR"),
    zh_Hans: () => import("#locales/zh_Hans"),
    zh_Hant: () => import("#locales/zh_Hant"),
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
    pseudo_LOCALE: /^pseudo/i,
    cs_CZ: /^cs([_-]|$)/i,
    de_DE: /^de([_-]|$)/i,
    es_ES: /^es([_-]|$)/i,
    fr_FR: /^fr([_-]|$)/i,
    it_IT: /^it([_-]|$)/i,
    ja_JP: /^ja([_-]|$)/i,
    ko_KR: /^ko([_-]|$)/i,
    nl_NL: /^nl([_-]|$)/i,
    pl_PL: /^pl([_-]|$)/i,
    ru_RU: /^ru([_-]|$)/i,
    tr_TR: /^tr([_-]|$)/i,
    /**
     * Traditional Chinese.
     *
     * The region subtag is required.
     */
    zh_Hant: /^zh[_-](TW|HK|MO|Hant)/i,
    /**
     * Simplified Chinese.
     *
     * The region subtag is optional.
     */
    zh_Hans: /^zh([_-](CN|SG|MY|Hans)|$)/i,
};

/**
 * A mapping of regex patterns to locale codes for matching user-supplied locale strings.
 *
 * @see {@linkcode LocalePatternRecord} for the source of this map.
 */
export const LocalePatternCodeMap = new Map<RegExp, TargetLocale>(
    Object.entries(LocalePatternRecord).map(([code, pattern]) => [pattern, code as TargetLocale]),
);
