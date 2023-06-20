import * as _enLocale from "@goauthentik/locales/en";

import type { LocaleModule } from "@lit/localize";
import { msg } from "@lit/localize";

import { AkLocale, LocaleRow } from "./types";

export const DEFAULT_FALLBACK = "en";

const enLocale: LocaleModule = _enLocale;

export { enLocale };

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
// French is currently an oddity; the translator provided the France regional version explicitly,
// and we fall back to that regardless of region. Sorry, Québécois.
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

// prettier-ignore
const LOCALE_TABLE: LocaleRow[] = [
    ["en",      /^en([_-]|$)/i,      () => msg("English"),               async () => await import("@goauthentik/locales/en")],
    ["es",      /^es([_-]|$)/i,      () => msg("Spanish"),               async () => await import("@goauthentik/locales/es")],
    ["de",      /^de([_-]|$)/i,      () => msg("German"),                async () => await import("@goauthentik/locales/de")],
    ["fr_FR",   /^fr([_-]|$)/i,      () => msg("French"),                async () => await import("@goauthentik/locales/fr_FR")],
    ["pl",      /^pl([_-]|$)/i,      () => msg("Polish"),                async () => await import("@goauthentik/locales/pl")],
    ["tr",      /^tr([_-]|$)/i,      () => msg("Turkish"),               async () => await import("@goauthentik/locales/tr")],
    ["zh-Hant", /^zh[_-](HK|Hant)/i, () => msg("Chinese (traditional)"), async () => await import("@goauthentik/locales/zh-Hant")],
    ["zh_TW",   /^zh[_-]TW$/i,       () => msg("Taiwanese Mandarin"),    async () => await import("@goauthentik/locales/zh_TW")],
    ["zh-Hans", /^zh(\b|_)/i,        () => msg("Chinese (simplified)"),  async () => await import("@goauthentik/locales/zh-Hans")],
];

export const LOCALES: AkLocale[] = LOCALE_TABLE.map(([code, match, label, locale]) => ({
    code,
    match,
    label,
    locale,
}));

export default LOCALES;
