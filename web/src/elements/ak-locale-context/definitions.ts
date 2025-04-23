import * as EnglishLocaleModule from "@goauthentik/locales/en";

import type { LocaleModule } from "@lit/localize";
import { msg } from "@lit/localize";

import { AKLocaleDefinition, LocaleRow } from "./types.js";

/**
 * The default ISO 639-1 language code.
 */
export const DEFAULT_LANGUAGE_CODE = "en";

/**
 * The default English locale module.
 */
export const DefaultLocaleModule: LocaleModule = EnglishLocaleModule;

// NOTE: This table cannot be made any shorter, despite all the repetition of syntax. Bundlers look
// for the `await import` string as a *string target* for doing alias substitution, so putting
// the import in some sort of abstracting function doesn't work. The same is true for the `msg()`
// function, which `localize` uses to find strings for extraction and translation. Likewise,
// because this is a file-level table, the `msg()` must be thunked so that they're re-run when
// the user changes the locale.

// NOTE: The matchers try to conform loosely to [RFC
// 5646](https://www.rfc-editor.org/rfc/rfc5646.txt), "Tags for the Identification of Languages." In
// practice, language tags have been seen using both hyphens and underscores, and the Chinese
// language uses both "regional" and "script" suffixes. The regexes use the language and any region
// or script.
//
// Chinese locales usually (but not always) use the script rather than region suffix. The default
// (optional) fallback for Chinese (zh) is "Chinese (simplified)", which is why it has that odd
// regex syntax at the end which means "match zh as long as it's not followed by a [:word:] token";
// Traditional script and the Taiwanese are attempted first, and if neither matches, anything
// beginning with that generic "zh" is mapped to "Chinese (simplified)."

// - Code for Lit/Locale
// - Regex for matching user-supplied locale.
// - Text Label
// - Locale loader.

const debug: LocaleRow = [
    "pseudo-LOCALE",
    /^pseudo/i,
    () => msg("Pseudolocale (for testing)"),
    () => import("@goauthentik/locales/pseudo-LOCALE"),
];

// prettier-ignore
const LOCALE_TABLE: readonly LocaleRow[] = [
    // English loaded when the application is first instantiated.
    ["en", /^en([_-]|$)/i,   () => msg("English"), () => Promise.resolve(DefaultLocaleModule)],
    ["de", /^de([_-]|$)/i,   () => msg("German"),  () => import("@goauthentik/locales/de")],
    ["es", /^es([_-]|$)/i,   () => msg("Spanish"), () => import("@goauthentik/locales/es")],
    ["fr", /^fr([_-]|$)/i,   () => msg("French"),  () => import("@goauthentik/locales/fr")],
    ["it", /^it([_-]|$)/i,   () => msg("Italian"), () => import("@goauthentik/locales/it")],
    ["ko", /^ko([_-]|$)/i,   () => msg("Korean"),  () => import("@goauthentik/locales/ko")],
    ["nl", /^nl([_-]|$)/i,   () => msg("Dutch"),   () => import("@goauthentik/locales/nl")],
    ["pl", /^pl([_-]|$)/i,   () => msg("Polish"),  () => import("@goauthentik/locales/pl")],
    ["ru", /^ru([_-]|$)/i,   () => msg("Russian"), () => import("@goauthentik/locales/ru")],
    ["tr", /^tr([_-]|$)/i,   () => msg("Turkish"), () => import("@goauthentik/locales/tr")],
    ["zh_TW", /^zh[_-]TW$/i, () => msg("Taiwanese Mandarin"), () => import("@goauthentik/locales/zh_TW")],
    ["zh-Hans", /^zh(\b|_)/i, () => msg("Chinese (simplified)"), () => import("@goauthentik/locales/zh-Hans")],
    ["zh-Hant", /^zh[_-](HK|Hant)/i, () => msg("Chinese (traditional)"), () => import("@goauthentik/locales/zh-Hant")],
    debug,
];

/**
 * Available locales, identified by their ISO 639-1 language code.
 */
export const AKLocalDefinitions: readonly AKLocaleDefinition[] = LOCALE_TABLE.map(
    ([languageCode, pattern, formatLabel, fetch]) => {
        return {
            languageCode,
            pattern,
            formatLabel,
            fetch,
        };
    },
);

export default AKLocalDefinitions;
