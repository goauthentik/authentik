import { allLocales, sourceLocale as SourceLanguageTag } from "../../../locale-codes.js";

import type { LocaleModule } from "@lit/localize";

export type TargetLanguageTag = (typeof allLocales)[number];
export const TargetLanguageTags = new Set<TargetLanguageTag>(allLocales);

/**
 * The language tag representing the pseudo-locale for testing.
 */
const PseudoLanguageTag = "en-XA" as const satisfies TargetLanguageTag;

export { PseudoLanguageTag, SourceLanguageTag };

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
    [SourceLanguageTag]: () => Promise.resolve(sourceTargetModule),
    [PseudoLanguageTag]: () => import("#locales/en-XA"),
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
