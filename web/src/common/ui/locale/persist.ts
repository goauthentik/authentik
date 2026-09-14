import { globalAK } from "#common/global";
import { TargetLanguageTag } from "#common/ui/locale/definitions";

//#region Cookie-persisted preference

/**
 * Name of the Django language cookie.
 *
 * @remarks
 * Must match `LANGUAGE_COOKIE_NAME` in `authentik/root/settings.py`. Django's stock
 * `LocaleMiddleware` reads this cookie to resolve the request locale, which is how a
 * client-side locale change survives the full page reload that applies it.
 */
export const LanguageCookieName = "authentik_language";

/**
 * Persist the given locale to the Django language cookie.
 *
 * @remarks
 * The cookie is not `httpOnly`, so it is writable from JS. It is scoped to the web base
 * path (matching `LANGUAGE_COOKIE_PATH`) and `SameSite=Lax`, which is sufficient because
 * the locale is only ever applied by a same-origin, top-level reload.
 */
export function persistLocale(languageTag: TargetLanguageTag): void {
    const path = globalAK().api.relBase || "/";
    // One year, matching Django's own `set_language` default expiry.
    const maxAge = 60 * 60 * 24 * 365;

    document.cookie = `${LanguageCookieName}=${encodeURIComponent(
        languageTag,
    )}; path=${path}; max-age=${maxAge}; SameSite=Lax`;
}

/**
 * Read the persisted locale from the Django language cookie, if present.
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
 * Locale is fixed for the lifetime of a page: switching persists the preference and
 * reloads so the server — the single resolver — re-renders every string (including
 * server-rendered flow challenges) in the new locale.
 */
export function applyLocaleChange(languageTag: TargetLanguageTag): void {
    persistLocale(languageTag);

    window.location.reload();
}

//#endregion
