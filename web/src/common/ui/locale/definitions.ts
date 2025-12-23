import { type allLocales, sourceLocale as SourceLanguageTag } from "../../../locale-codes.js";

import { UnwrapSet } from "#common/sets";

import type { LocaleModule } from "@lit/localize";

export type TargetLanguageTag = (typeof allLocales)[number];

/**
 * An enum-like record of language tag constants that require special handling.
 */
export const LanguageTag = {
    Source: SourceLanguageTag,
    Pseudo: "en-XA",
    HanSimplified: "zh-Hans",
    HanTraditional: "zh-Hant",
    Japanese: "ja-JP",
    Korean: "ko-KR",
} as const satisfies Record<string, TargetLanguageTag>;

/**
 * A set of **supported language tags** representing languages using Han scripts, i.e. Chinese.
 */
export const HanLanguageTags = new Set([
    LanguageTag.HanSimplified,
    LanguageTag.HanTraditional,
] as const satisfies TargetLanguageTag[]);

export type HanLanguageTag = UnwrapSet<typeof HanLanguageTags>;

/**
 * A set of **supported language tags** representing Chinese, Japanese, and Korean languages.
 */
export const CJKLanguageTags = new Set([
    LanguageTag.HanSimplified,
    LanguageTag.HanTraditional,
    LanguageTag.Japanese,
    LanguageTag.Korean,
] as const satisfies TargetLanguageTag[]);

export type CJKLanguageTag = UnwrapSet<typeof CJKLanguageTags>;

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
 * A record mapping locale codes to their respective module loaders.
 *
 * @remarks
 * The `import` statements **must** reference a locale module path,
 * as this is how ESBuild identifies which files to include in the build.
 */
export const LocaleLoaderRecord: Record<TargetLanguageTag, () => Promise<LocaleModule>> = {
    [LanguageTag.Source]: () => Promise.resolve(sourceTargetModule),
    [LanguageTag.Pseudo]: () => import("#locales/en-XA"),
    "cs-CZ": () => import("#locales/cs-CZ"),
    "de-DE": () => import("#locales/de-DE"),
    "es-ES": () => import("#locales/es-ES"),
    "fi-FI": () => import("#locales/fi-FI"),
    "fr-FR": () => import("#locales/fr-FR"),
    "it-IT": () => import("#locales/it-IT"),
    "ja-JP": () => import("#locales/ja-JP"),
    "ko-KR": () => import("#locales/ko-KR"),
    "nl-NL": () => import("#locales/nl-NL"),
    "pl-PL": () => import("#locales/pl-PL"),
    "pt-BR": () => import("#locales/pt-BR"),
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
export const LocalePatternRecord: Record<TargetLanguageTag, RegExp> = {
    [LanguageTag.Source]: /^en([_-]|$)/i,
    [LanguageTag.Pseudo]: /^en[_-](XA)/i,
    "cs-CZ": /^cs([_-]|$)/i,
    "de-DE": /^de([_-]|$)/i,
    "es-ES": /^es([_-]|$)/i,
    "fi-FI": /^fi([_-]|$)/i,
    "fr-FR": /^fr([_-]|$)/i,
    "it-IT": /^it([_-]|$)/i,
    "ja-JP": /^ja([_-]|$)/i,
    "ko-KR": /^ko([_-]|$)/i,
    "nl-NL": /^nl([_-]|$)/i,
    "pl-PL": /^pl([_-]|$)/i,
    "pt-BR": /^pt([_-]|$)/i,
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
export const LocalePatternCodeMap = new Map<RegExp, TargetLanguageTag>(
    Object.entries(LocalePatternRecord).map(([code, pattern]) => [
        pattern,
        code as TargetLanguageTag,
    ]),
);
