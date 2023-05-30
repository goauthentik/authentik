import { msg } from "@lit/localize";

import { AkLocale, LocaleRow } from "./types";

export const DEFAULT_FALLBACK = "en";

// NOTE: This table cannot be made any shorter, despite all the repetition. Bundlers look for the
// the `await import` string as a *string target* for doing alias substitution, so putting the alias
// in some sort of abstracting function doesn't work.

// - Code for Lit/Locale
// - Text Label
// - Locale loader.

// prettier-ignore
const LOCALE_TABLE: LocaleRow[] = [
    ["en", () => msg("English"), async () => await import("@goauthentik/locales/en")],
    ["es", () => msg("Spanish"), async () => await import("@goauthentik/locales/es")],
    ["de", () => msg("German"), async () => await import("@goauthentik/locales/de")],
    ["fr_FR", () => msg("French"), async () => await import("@goauthentik/locales/fr_FR")],
    ["pl", () => msg("Polish"), async () => await import("@goauthentik/locales/pl")],
    ["tr", () => msg("Turkish"), async () => await import("@goauthentik/locales/tr")],
    ["zh-CN", () => msg("Chinese (simplified)"), async () => await import("@goauthentik/locales/zh-Hans")],
    [ "zh_TW", () => msg("Taiwanese Mandarin"), async () => await import("@goauthentik/locales/zh_TW")],
    [ "zh-HK", () => msg("Chinese (traditional)"), async () => await import("@goauthentik/locales/zh-Hant")],
];

export const LOCALES: AkLocale[] = LOCALE_TABLE.map(([code, label, locale]) => ({
    code,
    label,
    locale,
}));

export default LOCALES;
