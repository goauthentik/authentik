import { globalAK } from "#common/global";
import { TargetLanguageTag } from "#common/ui/locale/definitions";

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

    document.cookie = `${LanguageCookieName}=${encodeURIComponent(
        languageTag,
    )}; path=${path}; max-age=${maxAge}; SameSite=Lax`;
}

/**
 * Read the locale persisted in the Django language cookie, if present.
 */
export function readPersistedLocale(): string | null {
    const prefix = `${LanguageCookieName}=`;

    for (const entry of document.cookie ? document.cookie.split(";") : []) {
        const cookie = entry.trim();

        if (cookie.startsWith(prefix)) {
            return decodeURIComponent(cookie.slice(prefix.length)) || null;
        }
    }

    return null;
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
