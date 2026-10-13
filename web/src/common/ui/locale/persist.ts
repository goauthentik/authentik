import { globalAK } from "#common/global";
import { TargetLanguageTag } from "#common/ui/locale/definitions";

import { parseCookie, stringifySetCookie } from "cookie";

//#region Cookie-persisted preference

/**
 * Name of the Django language cookie.
 *
 * @remarks
 *   Must match `LANGUAGE_COOKIE_NAME` in `authentik/root/settings.py`.
 *   Django `LocaleMiddleware` reads this cookie to resolve the request locale,
 *   allowing a client-side locale switch to persist across the reload that applies it.
 */
export const LanguageCookieName = "authentik_language";

/**
 * Persist the given locale to the Django language cookie.
 *
 * @remarks
 *   This cookie is intentionally not `httpOnly`, so JavaScript can write it.
 *   It is scoped to the web base path (matching `LANGUAGE_COOKIE_PATH`) and uses
 *   `SameSite=Lax`, which is sufficient because locale changes are applied via
 *   same-origin, top-level reloads.
 */
export function persistLocale(languageTag: TargetLanguageTag): void {
    const path = globalAK().api.relBase || "/";
    // One year, matching Django's `set_language` default expiration.
    const maxAge = 60 * 60 * 24 * 365;

    document.cookie = stringifySetCookie({
        name: LanguageCookieName,
        value: languageTag,
        path,
        maxAge,
        sameSite: "lax",
        secure: location.protocol === "https:",
    });
}

/**
 * Read the locale persisted in the Django language cookie, if present.
 */
export function readPersistedLocale(): string | null {
    return parseCookie(document.cookie)[LanguageCookieName] || null;
}

//#endregion

//#region Applying a locale change

/**
 * Persist the given locale and reload the page to apply it.
 *
 * @remarks
 *   Locale is fixed for the lifetime of a page.
 *   Switching locale persists the preference and reloads so the server re-renders all strings,
 *   including server-rendered flow challenges, in the new locale.
 */
export function applyLocaleChange(languageTag: TargetLanguageTag): void {
    persistLocale(languageTag);

    window.location.reload();
}

//#endregion
