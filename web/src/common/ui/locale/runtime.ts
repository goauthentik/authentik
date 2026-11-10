/**
 * @remarks
 *   The locale is fixed for the lifetime of a page; switching reloads it.
 *   Keep this module free of `msg()` calls, including transitively, since it
 *   runs before any catalog is loaded.
 * @file The page's lit-localize runtime.
 */

import { sourceLocale, targetLocales } from "../../../locale-codes.js";

import { globalAK } from "#common/global";
import { LocaleLoaderRecord, TargetLanguageTag } from "#common/ui/locale/definitions";
import { isTargetLanguageTag } from "#common/ui/locale/utils";

import { configureLocalization, LocaleModule } from "@lit/localize";

function loadLocale(locale: string): Promise<LocaleModule> {
    if (!isTargetLanguageTag(locale)) {
        throw new TypeError(`Unsupported locale code: ${locale}`);
    }

    return LocaleLoaderRecord[locale]();
}

/**
 * The page-wide localization runtime.
 */
export const localization = configureLocalization({
    sourceLocale,
    targetLocales,
    loadLocale,
});

/**
 * Load the catalog for the page's locale and mark the document with it.
 *
 * @remarks
 *   Await this before importing any module that calls `msg()` at module level.
 */
export async function initializeLocale(
    languageTag: TargetLanguageTag = globalAK().locale,
): Promise<void> {
    try {
        await localization.setLocale(languageTag);
    } catch (error) {
        console.error(`authentik/locale: Failed to load "${languageTag}", using source`, error);
    }

    document.documentElement.lang = localization.getLocale();
}
